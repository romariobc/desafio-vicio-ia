# -*- coding: utf-8 -*-
"""
Script de Reprodução em Tempo de Decisão (ZERO chamadas a LLM ou encoders externos).

Gera a partir dos anexos e dos artefatos versionados em `artefatos/`:
1. `publicacao.csv` (659 linhas com id, decisao, tema_central_id, extras_ids, confianca, motivo)
2. `previsao.txt` (estimativa pontual e intervalar de precisão e cobertura fora da folha_verdade)
3. `artefatos/metricas_validacao.json` (auditoria completa das 5 dobras, ablação de formato e benchmark de escala)
"""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path

from modelo_sistema import ClassificadorTopicosJuridicos, intervalo_wilson

PASTA_ETAPA2 = Path(__file__).resolve().parent.parent
LIMIAR_PUBLICAR = 0.575
LIMIAR_FORA = 0.70
DESCONTO_OTIMISMO_SELECAO = 0.015


def gerar_texto_previsao(
    relatorio_cv: dict,
    simulacao_coorte: dict,
    stats_559: dict,
) -> str:
    prec_oof = relatorio_cv["precisao_publicar_oof"]
    cov_559 = stats_559["cobertura_publicar_559"]
    n_pub_559 = stats_559["publicar"]
    n_tot_559 = stats_559["total_avaliadas_fora_folha"]

    # Estimativa pontual e intervalar sem ajustes arbitrários:
    # - A precisão observada nos 5 folds externos (OOF) é 60/62 = 96.77%, com intervalo binomial
    #   de Wilson de 95% em [88.98%, 99.11%] e de 90% em [90.69%, 98.93%].
    # - Como pesos, âncoras e o limiar (0.575) foram selecionados avaliando o desempenho nas 100
    #   referências, aplicamos um desconto explícito de 1.5 p.p. para otimismo de seleção pós-hoc
    #   e mudança de coorte (96.77% - 1.50% -> 0.95), mantendo o intervalo de Wilson de 95% puro
    #   sem somas artificiais (0.89-0.99).
    prec_prevista = round(prec_oof - DESCONTO_OTIMISMO_SELECAO, 2)
    ic_prec_lo = round(relatorio_cv["precisao_ic95_wilson"][0], 2)
    ic_prec_hi = round(relatorio_cv["precisao_ic95_wilson"][1], 2)

    # A cobertura realizada no lote entregue de 559 questões fora da folha_verdade já é conhecida
    # exatamente (319/559 = 57.07%); o intervalo de Wilson de 95% reflete a variação amostral
    # esperada para novos lotes de mesma dimensão extraídos dessa distribuição.
    cov_prevista = round(cov_559, 2)
    cov_lo, cov_hi = intervalo_wilson(n_pub_559, n_tot_559, z=1.96)
    cov_lo_r = round(cov_lo, 2)
    cov_hi_r = round(cov_hi, 2)

    c_ant = stats_559["por_coorte"]["antiga_Q0001_Q0359"]
    c_nov = stats_559["por_coorte"]["nova_Q0360_Q0659"]

    linhas = [
        f"precisao_prevista: {prec_prevista:.2f}",
        f"precisao_intervalo: {ic_prec_lo:.2f}-{ic_prec_hi:.2f}",
        f"cobertura_prevista: {cov_prevista:.2f}",
        f"cobertura_intervalo: {cov_lo_r:.2f}-{cov_hi_r:.2f}",
        "",
        "Como chegamos nesses números (separando medições verificáveis de hipóteses de extrapolação):",
        "1. Medição Verificável na Validação Cruzada de 5 Dobras (folha_verdade.csv):",
        f"   - Acurácia top-1 global (sem abstenção): {relatorio_cv['acertos_top1_total']}/100 ({relatorio_cv['acuracia_top1_total']:.1%}), "
        f"sendo {relatorio_cv['acertos_top1_total']}/92 ({relatorio_cv['acuracia_top1_em_taxonomia']:.2%}) nas questões pertencentes à taxonomia ativa.",
        f"   - No limiar de publicação (confianca >= {LIMIAR_PUBLICAR:.3f}, score_fora < {LIMIAR_FORA:.2f} e regra de convergência mínima entre canais), "
        f"o sistema publicou {relatorio_cv['publicadas_oof']}/100 questões nos folds externos e acertou {relatorio_cv['acertos_publicadas_oof']}/{relatorio_cv['publicadas_oof']} "
        f"(precisão observada OOF = {prec_oof:.2%}, margem pontual de +{(prec_oof - 0.95)*100:.2f} p.p. sobre 95%, Brier Score = {relatorio_cv['brier_score_oof']:.4f}).",
        f"   - O intervalo `precisao_intervalo: {ic_prec_lo:.2f}-{ic_prec_hi:.2f}` é o intervalo binomial de Wilson de 95% exato para {relatorio_cv['acertos_publicadas_oof']}/{relatorio_cv['publicadas_oof']} "
        f"({relatorio_cv['precisao_ic95_wilson'][0]:.4f} a {relatorio_cv['precisao_ic95_wilson'][1]:.4f}), sem truncamentos ou somas artificiais. "
        "Com n=62 publicações, mesmo 62/62 acertos teria limite inferior de Wilson 95% de 94.17%; logo, a amplitude inferior decorre do tamanho amostral finito da folha_verdade.",
        f"   - A previsão pontual (`{prec_prevista:.2f}`) aplica um desconto conservador de {DESCONTO_OTIMISMO_SELECAO*100:.1f} p.p. sobre os {prec_oof:.2%} observados "
        "para absorver o otimismo de seleção pós-hoc (pesos, âncoras e limiar foram ajustados analisando erros nas 100 referências).",
        "",
        "2. Cobertura Realizada nas 559 Questões Avaliadas e Diferença entre Coortes:",
        f"   - Nas 559 questões fora da folha_verdade.csv, a cobertura realizada em `publicacao.csv` é conhecida exatamente: "
        f"{n_pub_559}/{n_tot_559} = {cov_559:.2%} (`publicar`), com {stats_559['revisar']}/{n_tot_559} ({stats_559['revisar']/n_tot_559:.2%}) em `revisar` "
        f"e {stats_559['fora']}/{n_tot_559} ({stats_559['fora']/n_tot_559:.2%}) em `fora`. O intervalo `{cov_lo_r:.2f}-{cov_hi_r:.2f}` expressa o IC 95% de Wilson para novos lotes.",
        f"   - Coorte antiga (Q0001-Q0359, fora da folha: {c_ant['total']} questões): publicadas {c_ant['publicar']}/{c_ant['total']} ({c_ant['publicar']/c_ant['total']:.1%}), "
        f"com concordância simultânea top-1 léxico+semântico em {c_ant['taxa_pub_lex1_e_sem1']:.1%} e top-2 em {c_ant['taxa_pub_lex2_e_sem2']:.1%}.",
        f"   - Coorte nova (Q0360-Q0659: {c_nov['total']} questões): publicadas {c_nov['publicar']}/{c_nov['total']} ({c_nov['publicar']/c_nov['total']:.1%}), "
        f"com concordância simultânea top-1 léxico+semântico em {c_nov['taxa_pub_lex1_e_sem1']:.1%} e top-2 em {c_nov['taxa_pub_lex2_e_sem2']:.1%}.",
        "",
        "3. Limites da Extrapolação para a Coorte Nova (Q0360-Q0659):",
        "   - Como todas as 100 referências da folha_verdade pertencem a Q0001-Q0359, o desempenho real em Q0360-Q0659 não é observável antes da correção da banca.",
        f"   - Em ablação controlada do formato estrutural (incorporando `comando` ao final de `enunciado_html` e esvaziando `comando` nas 100 referências, com vetores MiniLM fixos), "
        f"o extrator `extrair_foco_e_corpo` manteve {simulacao_coorte['acertos_top1_total']}/100 acertos top-1 e precisão OOF de {simulacao_coorte['precisao_publicar_oof']:.2%} "
        f"({simulacao_coorte['acertos_publicadas_oof']}/{simulacao_coorte['publicadas_oof']}), validando a resiliência estrutural à ausência do campo `comando` separado.",
    ]
    return "\n".join(linhas) + "\n"


def main() -> None:
    t0 = time.perf_counter()
    clf = ClassificadorTopicosJuridicos(PASTA_ETAPA2)

    relatorio_cv = clf.avaliar_validacao_cruzada(
        limiar_publicar=LIMIAR_PUBLICAR,
        limiar_fora=LIMIAR_FORA,
    )
    t_antes_inf = time.perf_counter()
    linhas_pub, stats_559 = clf.executar_inferencia_completa(
        limiar_publicar=LIMIAR_PUBLICAR,
        limiar_fora=LIMIAR_FORA,
    )
    tempo_decisao_659 = time.perf_counter() - t0

    simulacao_coorte = clf.avaliar_simulacao_formato_coorte_nova(
        limiar_publicar=LIMIAR_PUBLICAR,
        limiar_fora=LIMIAR_FORA,
    )
    benchmark_50k = clf.benchmark_escala_50k(tempo_decisao_659_s=tempo_decisao_659)

    caminho_pub = PASTA_ETAPA2 / "publicacao.csv"
    campos = ["id", "decisao", "tema_central_id", "extras_ids", "confianca", "motivo"]
    with caminho_pub.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas_pub)

    caminho_prev = PASTA_ETAPA2 / "previsao.txt"
    texto_prev = gerar_texto_previsao(relatorio_cv, simulacao_coorte, stats_559)
    caminho_prev.write_text(texto_prev, encoding="utf-8")

    caminho_metricas = PASTA_ETAPA2 / "artefatos" / "metricas_validacao.json"
    resumo_completo = {
        "tempo_execucao_segundos": round(time.perf_counter() - t0, 3),
        "tempo_inferencia_659_segundos": round(time.perf_counter() - t_antes_inf, 3),
        "validacao_cruzada_100_refs": relatorio_cv,
        "simulacao_formato_coorte_nova_100_refs": simulacao_coorte,
        "inferencia_559_avaliadas": stats_559,
        "benchmark_escala_50k": benchmark_50k,
        "distribuicao_659_total": {
            "publicar": sum(1 for r in linhas_pub if r["decisao"] == "publicar"),
            "revisar": sum(1 for r in linhas_pub if r["decisao"] == "revisar"),
            "fora": sum(1 for r in linhas_pub if r["decisao"] == "fora"),
        },
    }
    caminho_metricas.write_text(
        json.dumps(resumo_completo, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    dt = time.perf_counter() - t0
    print(f"[OK] Reprodução concluída em {dt:.2f}s (ZERO chamadas a LLM/encoders).")
    print(
        f" - Validação Cruzada (100 refs): Top-1 = {relatorio_cv['acertos_top1_total']}/100 "
        f"({relatorio_cv['acuracia_top1_em_taxonomia']:.2%} em taxonomia) | "
        f"Precisão Publicar OOF = {relatorio_cv['acertos_publicadas_oof']}/{relatorio_cv['publicadas_oof']} "
        f"({relatorio_cv['precisao_publicar_oof']:.2%})"
    )
    print(
        f" - Simulação Formato Coorte Nova (100 refs): Top-1 = {simulacao_coorte['acertos_top1_total']}/100 | "
        f"Precisão Publicar OOF = {simulacao_coorte['acertos_publicadas_oof']}/{simulacao_coorte['publicadas_oof']} "
        f"({simulacao_coorte['precisao_publicar_oof']:.2%})"
    )
    print(
        f" - Questões fora da folha (559): publicar={stats_559['publicar']} ({stats_559['cobertura_publicar_559']:.2%}), "
        f"revisar={stats_559['revisar']}, fora={stats_559['fora']}"
    )
    print(f" - Arquivos gerados: {caminho_pub.name}, {caminho_prev.name}, artefatos/{caminho_metricas.name}")


if __name__ == "__main__":
    main()
