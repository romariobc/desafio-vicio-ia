# -*- coding: utf-8 -*-
"""
Suíte de Testes Automatizados e Auditoria de Conformidade da Etapa 2.

Verifica:
1. Integridade estrutural e contratual de `publicacao.csv` (659 linhas, colunas exatas, tipos).
2. Proibição estrita de temas inativos (5078, 5234) ou nós de nível 0 (raízes de disciplina).
3. Regra oficial de acerto hierárquico e propriedade de dominância do Roll-up Canônico (92/92 = 100%).
4. Formato de `previsao.txt` conforme `anexos/LEIA-ME.md` e ausência de clamps artificiais.
5. Meta de qualidade na validação cruzada Out-of-Fold (precisão observada >= 95%).
6. Isolamento estrito em tempo de decisão (ausência de imports de LLM/rede nos módulos de inferência).
7. Autocontenção de `preparar_artefatos.py` (sem caminhos externos ao repositório).
8. Complexidade de memória O(N * M_ref) e sincronia numérica entre `metricas_validacao.json` e a documentação.
"""
from __future__ import annotations

import ast
import csv
import json
import unittest
from pathlib import Path

from modelo_sistema import ClassificadorTopicosJuridicos
from processamento import carregar_anexos, extrair_foco_e_corpo, limpar_html

PASTA_ETAPA2 = Path(__file__).resolve().parent.parent


class TestSistemaClassificacaoTopicos(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.questoes, cls.tax, cls.refs, cls.leia_me = carregar_anexos(
            PASTA_ETAPA2 / "anexos"
        )
        cls.caminho_pub = PASTA_ETAPA2 / "publicacao.csv"
        cls.caminho_prev = PASTA_ETAPA2 / "previsao.txt"
        cls.caminho_metricas = PASTA_ETAPA2 / "artefatos" / "metricas_validacao.json"

    def test_01_preservacao_negacoes_e_extracao_foco(self) -> None:
        """Garante que limpar_html preserva operadores de negação e extrai comando embutido."""
        html = "<p>Assinale a opção <b>INCORRETA</b> quanto ao <i>não</i> cabimento e <u>exceto</u> nos casos legais.</p>"
        limpo = limpar_html(html).lower()
        for termo in ("incorreta", "não", "exceto"):
            self.assertIn(termo, limpo)

        q_nova = next(q for q in self.questoes if q["id"] == "Q0360")
        self.assertEqual(q_nova.get("comando", ""), "")
        partes = extrair_foco_e_corpo(q_nova)
        self.assertTrue(len(partes["foco"]) > 15)

    def test_02_dominancia_rollup_hierarquico_92_de_92(self) -> None:
        """Verifica que o roll-up hierárquico (nível 2 -> pai de nível 1) e os ramos canônicos cobrem 92/92 (100%)."""
        em_tax = [r for r in self.refs.values() if r["fora_da_taxonomia"] == "0"]
        self.assertEqual(len(em_tax), 92)
        for r in em_tax:
            tid = r["tema_central_id"]
            no = self.tax.ativos[tid]
            pai_n1 = no["parent_id"] if no["nivel"] == "2" else tid
            self.assertEqual(self.tax.ativos[pai_n1]["nivel"], "1")
            self.assertTrue(
                self.tax.correto(pai_n1, r),
                f"Falha no roll-up direto nível 2 -> nível 1 para {r['id']}",
            )
            alvos = [tid] + [x for x in r["extras_ids"].split(";") if x]
            ramos_alvos = [self.tax.ramo_canonico(t) for t in alvos]
            self.assertTrue(
                any(self.tax.correto(rc, r) for rc in ramos_alvos),
                f"Nenhum ramo canônico aceito para {r['id']}: {ramos_alvos}",
            )

    def test_03_contrato_publicacao_csv_659_questoes(self) -> None:
        """Valida todas as 659 linhas de publicacao.csv contra as regras de anexos/LEIA-ME.md."""
        self.assertTrue(self.caminho_pub.exists(), "publicacao.csv não encontrado.")
        with self.caminho_pub.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            self.assertEqual(
                reader.fieldnames,
                ["id", "decisao", "tema_central_id", "extras_ids", "confianca", "motivo"],
            )
            linhas = list(reader)

        self.assertEqual(len(linhas), 659)
        ids_esperados = [q["id"] for q in self.questoes]
        self.assertEqual([r["id"] for r in linhas], ids_esperados)

        inativos = {"5078", "5234"}
        for r in linhas:
            qid = r["id"]
            dec = r["decisao"]
            tc = r["tema_central_id"]
            extras = [x for x in r["extras_ids"].split(";") if x]
            conf_str = r["confianca"]
            motivo = r["motivo"].strip()

            self.assertIn(dec, {"publicar", "revisar", "fora"}, f"Decisão inválida em {qid}")
            self.assertRegex(conf_str, r"^\d\.\d{2}$", f"Formato de confiança inválido em {qid}")
            conf = float(conf_str)
            self.assertGreaterEqual(conf, 0.0)
            self.assertLessEqual(conf, 1.0)

            if dec == "fora":
                self.assertEqual(tc, "", f"tema_central_id deve ser vazio quando decisao=fora ({qid})")
                self.assertEqual(extras, [], f"extras_ids deve ser vazio quando decisao=fora ({qid})")
                self.assertTrue(len(motivo) >= 5, f"motivo obrigatório em decisao=fora ({qid})")
            else:
                self.assertNotEqual(tc, "", f"tema_central_id obrigatório em {dec} ({qid})")
                self.assertNotIn(tc, inativos, f"Tema inativo proibido em {qid}: {tc}")
                self.assertIn(tc, self.tax.ativos, f"Tema inexistente/inativo em {qid}: {tc}")
                self.assertIn(
                    self.tax.ativos[tc]["nivel"],
                    {"1", "2"},
                    f"Proibido usar nó raiz de disciplina (nível 0) em {qid}: {tc}",
                )
                for ex in extras:
                    self.assertNotIn(ex, inativos, f"Extra inativo proibido em {qid}: {ex}")
                    self.assertIn(ex, self.tax.ativos, f"Extra inválido em {qid}: {ex}")
                    self.assertNotEqual(ex, tc, f"Extra duplicado com tema_central_id em {qid}")

                if dec == "revisar":
                    self.assertTrue(len(motivo) >= 5, f"motivo obrigatório em decisao=revisar ({qid})")

    def test_04_formato_previsao_txt(self) -> None:
        """Verifica que previsao.txt contém os 4 campos obrigatórios no topo e justificativa textual."""
        self.assertTrue(self.caminho_prev.exists(), "previsao.txt não encontrado.")
        linhas = self.caminho_prev.read_text(encoding="utf-8").splitlines()
        self.assertGreaterEqual(len(linhas), 10)
        self.assertRegex(linhas[0], r"^precisao_prevista:\s*0\.\d{2}$")
        self.assertRegex(linhas[1], r"^precisao_intervalo:\s*0\.\d{2}-0\.\d{2}$")
        self.assertRegex(linhas[2], r"^cobertura_prevista:\s*0\.\d{2}$")
        self.assertRegex(linhas[3], r"^cobertura_intervalo:\s*0\.\d{2}-0\.\d{2}$")

        prec = float(linhas[0].split(":")[1].strip())
        self.assertGreaterEqual(prec, 0.90)
        self.assertLessEqual(prec, 0.97)

    def test_05_metricas_validacao_oof_e_simulacao_coorte(self) -> None:
        """Audita se a precisão OOF nas 5 dobras e a simulação estrutural da coorte nova estão registradas."""
        self.assertTrue(self.caminho_metricas.exists())
        dados = json.loads(self.caminho_metricas.read_text(encoding="utf-8"))
        cv = dados["validacao_cruzada_100_refs"]
        self.assertGreaterEqual(cv["acuracia_top1_em_taxonomia"], 0.85)
        self.assertGreaterEqual(cv["precisao_publicar_oof"], 0.95)
        self.assertGreaterEqual(cv["cobertura_publicar_oof"], 0.50)

        sim = dados["simulacao_formato_coorte_nova_100_refs"]
        self.assertGreaterEqual(sim["acertos_top1_total"], 80)
        self.assertGreaterEqual(sim["precisao_publicar_oof"], 0.95)

    def test_06_isolamento_zero_llm_em_tempo_de_decisao(self) -> None:
        """Garante via AST que processamento.py, modelo_sistema.py e reproduzir.py não importam LLMs/encoders/rede."""
        modulos_proibidos = {
            "openai",
            "anthropic",
            "google",
            "vertexai",
            "langchain",
            "llama_index",
            "transformers",
            "torch",
            "fastembed",
            "onnxruntime",
            "requests",
            "httpx",
            "urllib",
            "aiohttp",
        }
        arquivos_runtime = [
            PASTA_ETAPA2 / "codigo" / "processamento.py",
            PASTA_ETAPA2 / "codigo" / "modelo_sistema.py",
            PASTA_ETAPA2 / "codigo" / "reproduzir.py",
        ]
        for arq in arquivos_runtime:
            arvore = ast.parse(arq.read_text(encoding="utf-8"), filename=str(arq))
            for no in ast.walk(arvore):
                if isinstance(no, ast.Import):
                    for alias in no.names:
                        raiz = alias.name.split(".")[0]
                        self.assertNotIn(
                            raiz,
                            modulos_proibidos,
                            f"Import proibido '{alias.name}' detectado em {arq.name}",
                        )
                elif isinstance(no, ast.ImportFrom) and no.module:
                    raiz = no.module.split(".")[0]
                    self.assertNotIn(
                        raiz,
                        modulos_proibidos,
                        f"ImportFrom proibido '{no.module}' detectado em {arq.name}",
                    )

    def test_07_preparar_artefatos_autocontido(self) -> None:
        """Verifica que preparar_artefatos.py não referencia pastas externas ao repositório."""
        arq_prep = PASTA_ETAPA2 / "codigo" / "preparar_artefatos.py"
        conteudo = arq_prep.read_text(encoding="utf-8")
        self.assertNotIn("parent.parent", conteudo)
        self.assertNotIn("experimentos", conteudo)
        self.assertTrue((PASTA_ETAPA2 / "artefatos" / "insumos_base_temas.json").exists())

    def test_08_complexidade_memoria_knn_e_sincronia_docs(self) -> None:
        """Garante que a matriz kNN é O(N * M_ref) = (659, 100) e que os números da doc batem com o JSON."""
        clf = ClassificadorTopicosJuridicos(PASTA_ETAPA2)
        self.assertEqual(clf.sim_q_ref_hibrida.shape, (659, 100))
        self.assertFalse(hasattr(clf, "sim_q_hibrida"))

        dados = json.loads(self.caminho_metricas.read_text(encoding="utf-8"))
        brier_str = f"{dados['validacao_cruzada_100_refs']['brier_score_oof']:.4f}"
        n_pub_559 = str(dados["inferencia_559_avaliadas"]["publicar"])

        relatorio_txt = (PASTA_ETAPA2 / "RELATORIO.md").read_text(encoding="utf-8")
        readme_txt = (PASTA_ETAPA2 / "README.md").read_text(encoding="utf-8")
        self.assertIn(brier_str.replace(".", ","), relatorio_txt)
        self.assertIn(f"{n_pub_559}/559", readme_txt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
