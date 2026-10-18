"""Audita o desenho e a composição SEM comparar rótulos humanos com o modelo."""
import collections
import csv
import hashlib
import json
import math
import random
import re
from pathlib import Path

BASE=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent

def ler_csv(p,delimiter=','):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=delimiter))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mdtable(dist):
    lines=['| Grupo | Lote | % lote | Amostra | % amostra |','|---|---:|---:|---:|---:|']
    for x in dist:lines.append(f"| {x['grupo']} | {x['populacao_n']} | {x['populacao_pct']:.2f}% | {x['amostra_n']} | {x['amostra_pct']:.2f}% |")
    return '\n'.join(lines)

def main():
    site=BASE/'microsite_avaliacao_cega_30.html'
    payload=json.loads(re.search(r'<script id="experimento" type="application/json">(.*?)</script>',site.read_text(encoding='utf-8'),re.S).group(1))
    ids=[q['id'] for q in payload['questoes']];sample=set(ids)
    qs=[json.loads(s) for s in (BASE/'dados/questoes.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
    temas={t['tema_id']:t for t in ler_csv(BASE/'dados/temas_ativos.csv')}
    rows=ler_csv(BASE/'publicacao.csv');byid={r['id']:r for r in rows}
    drawn=random.Random(int(payload['registro']['sorteio']['semente_hex'],16)).sample(sorted(qs,key=lambda q:q['id']),30)
    assert len(qs)==359 and len(ids)==len(sample)==30 and ids==[q['id'] for q in drawn]
    def disciplina(r):return temas[r['tema_central_id']]['disciplina'] if r['tema_central_id'] else 'Sem tema (fora)'
    def dist(pop,sam,fn):
        pc=collections.Counter(fn(r) for r in pop);sc=collections.Counter(fn(r) for r in sam)
        return [{'grupo':k,'populacao_n':pc[k],'populacao_pct':100*pc[k]/len(pop),
                 'amostra_n':sc[k],'amostra_pct':100*sc[k]/len(sam)} for k in pc]
    sam=[byid[i] for i in ids];pub=[r for r in rows if r['decisao']=='publicar'];sam_pub=[r for r in sam if r['decisao']=='publicar']
    N=len(rows);n=len(sam);Np=len(pub);np=len(sam_pub)
    parts=json.loads((BASE/'referencia/particoes.json').read_text(encoding='utf-8'))
    ajustes={r['id'] for r in ler_csv(BASE/'decisoes/ajustes_r3.psv','|')}
    exports=[]
    # Somente completude, IDs, metadados e presença de rótulo são inspecionados.
    # Não calculamos concordância, acerto, precisão ou distribuição dos temas humanos.
    for path in sorted(BASE.glob('avaliacao_cega_30_*.json')):
        data=json.loads(path.read_text(encoding='utf-8-sig'));resp=data['respostas']
        exports.append({'arquivo':path.name,'sha256':sha(path),'respostas':len(resp),
            'mesmos_ids_sorteados':{r['id'] for r in resp}==sample,
            'registro_experimento_confere':data['registro_experimento']==payload['registro'],
            'concluidas_marcadas_no_arquivo':sum(r.get('concluida') is True for r in resp),
            'classificadas_sem_id':sum(r.get('situacao')=='classificada' and not r.get('tema_referencia_id') for r in resp),
            'fora_sem_justificativa':sum(r.get('situacao')=='fora' and not r.get('observacao','').strip() for r in resp),
            'exposicao_previa':dict(collections.Counter(r.get('exposicao_previa','nao_informado') for r in resp))})
    incompatible=Np-math.ceil(.95*Np)+1
    def zero(n):return math.comb(Np-incompatible,n)/math.comb(Np,n) if n<=Np-incompatible else 0
    sizes={str(a):next(k for k in range(1,Np+1) if zero(k)<=a) for a in (.05,.025)}
    study={'escopo':'Representatividade e completude antes da comparação de rótulos',
        'resultado':'Amostra probabilística válida para auditoria exploratória do lote; insuficiente para comprovar precisão >=95% ou qualidade por disciplina/tema.',
        'registro_sorteio':payload['registro']['sorteio'],'sorteio_reproduzido':True,
        'N':N,'n':n,'probabilidade_inclusao':n/N,'publicadas_N':Np,'publicadas_n':np,
        'decisoes':dist(rows,sam,lambda r:r['decisao']),
        'disciplinas_propostas':dist(rows,sam,disciplina),
        'disciplinas_propostas_entre_publicadas':dist(pub,sam_pub,disciplina),
        'niveis':dist(rows,sam,lambda r:temas[r['tema_central_id']]['nivel'] if r['tema_central_id'] else 'fora'),
        'sobreposicao_calibracao':sorted(sample&set(parts['calibracao'])),
        'sobreposicao_reservado_anterior':sorted(sample&set(parts['avaliacao_reservada'])),
        'sobreposicao_ajustes_r3':sorted(sample&ajustes),
        'observacao_ajustes':'Receber ajuste sem acesso a rótulo humano não constitui, sozinho, vazamento; distinguir de reutilizar rótulos da calibração.',
        'exportacoes':exports,'rotulos_humanos_comparados_com_modelo':False,
        'cenario_hipotetico_zero_erros':{
            'nao_e_resultado_observado':True,'publicadas_n':np,
            'wilson_bilateral_95_inferior':np/(np+1.96**2),
            'clopper_pearson_unilateral_95_inferior':.05**(1/np),
            'N_finito':Np,'erros_minimos_para_violar_95':incompatible,
            'probabilidade_nao_detectar_esses_erros':zero(np),
            'amostra_minima_zero_erros_teste_exato_finito_unilateral_95':sizes['0.05'],
            'amostra_minima_zero_erros_cauda_025':sizes['0.025'],
            'restricoes':'Política fixa, amostra aleatória de publicadas, referência adequada, plano fixado antes de ver acertos; números não são tamanho universal para qualquer resultado.'},
        'margem_normal_aproximada_pior_caso_com_correcao_finita':1.96*math.sqrt(.25/n*(N-n)/(N-1)),
        'fontes_sha256':{str(p.relative_to(BASE)).replace('\\','/'):sha(p) for p in [site,BASE/'publicacao.csv',BASE/'dados/questoes.jsonl',BASE/'dados/temas_ativos.csv']},
        'referencias':['https://www150.statcan.gc.ca/n1/edu/power-pouvoir/ch13/prob/5214899-eng.htm','https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbici.htm']}
    (OUT/'representatividade.json').write_text(json.dumps(study,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=f'''# Auditoria da amostra cega — antes da comparação de resultados

## Parecer

O sorteio das 30 questões é válido e reproduzível como amostragem aleatória simples sem reposição do lote de 359. Isso permite uma avaliação exploratória baseada em probabilidades de inclusão conhecidas. Não assegura uma miniatura proporcional de todas as disciplinas nem tamanho suficiente para demonstrar precisão mínima de 95%. O parecer foi obtido sem comparar rótulos humanos e automáticos.

## Verificação do desenho

- 30 IDs únicos; todos pertencem ao lote. A semente reproduz os mesmos IDs e a mesma ordem.
- Cada questão teve probabilidade de inclusão 30/359 = {100*n/N:.2f}%.
- Questões não foram escolhidas em função de acertos observados. O sorteio não filtrou pela decisão/confiança do modelo.
- Fontes e registro do experimento conferidos; a exportação humana contém os mesmos 30 IDs.
- As proporções de disciplina abaixo são as propostas pelo pipeline, não rótulos humanos independentes.

## Composição por decisão

{mdtable(study['decisoes'])}

O foco do desafio é a precisão das publicadas: o denominador de avaliação correspondente é 26, não 30. Não há nenhuma das 4 exclusões na amostra. A ausência não invalida o sorteio: a chance de selecionar zero das quatro exclusões neste desenho é aproximadamente 70,43%. Entretanto, o experimento não audita essa fila.

## Composição por disciplina proposta

{mdtable(study['disciplinas_propostas'])}

Penal está sobrerrepresentado e Processo Penal sub-representado na amostra obtida. Isso pode ocorrer ao acaso num sorteio válido; não é prova de manipulação nem motivo para substituir questões após a avaliação. Os grupos pequenos não sustentam conclusões separadas por disciplina.

### Apenas as publicadas (população-alvo do requisito de precisão)

{mdtable(study['disciplinas_propostas_entre_publicadas'])}

As quatro publicadas de Processo Penal não bastam para uma conclusão robusta específica sobre essa disciplina. Não ajustar pesos depois de observar erros para obter um resultado melhor. Uma análise ponderada, se necessária, deverá ser especificada e reportada como análise adicional, incluindo sua maior incerteza.

## Independência e exposição prévia

Três IDs já tinham rótulos na calibração: {', '.join(study['sobreposicao_calibracao'])}. Não há sobreposição com os 18 do reservado anterior. Dos 30, 27 não pertenciam à revisão humana antiga. Q0141 recebeu ajuste semântico na R3; isso não significa que seu novo rótulo humano tenha sido visto antes.

Para auditoria do lote fixo, o sorteio continua válido mesmo incluindo itens usados no desenvolvimento. Para avaliar generalização em itens sem referência prévia, deve-se distinguir o subconjunto sem rótulos de desenvolvimento, que é outro alvo de inferência. Não chamar os 30 de conjunto totalmente novo e independente. O registro de exposição prévia está como não informado nas 30 respostas: a interface oculta sugestões, mas a memória do avaliador não está controlada.

## Tamanho e limite da evidência

Sem olhar os resultados, considere o melhor cenário possível: 26/26 publicadas corretas. O limite inferior Wilson bilateral de 95% seria cerca de 87,13%; o limite inferior exato binomial unilateral de 95% seria cerca de 89,12%. São métodos diferentes; nenhum provaria a meta mínima de 95%.

No lote finito de 316 publicadas, 16 erros já violariam a meta. Mesmo existindo esses 16 erros, a chance de um sorteio de 26 publicadas não encontrar nenhum seria {100*zero(np):.2f}%. Assim, zero erros na amostra ainda seria compatível com um lote abaixo da meta.

Como cenário de planejamento (não resultado ou exigência universal): 53 publicadas aleatórias, todas corretas, permitiriam rejeitar a hipótese de 16 ou mais erros no lote de 316 em teste exato unilateral de 5%; a cauda de 2,5% exigiria 64 sem erro. Se aparecer erro, os tamanhos mudam. Para novos lotes/modelo binomial, 59 sem erro é o cenário unilateral exato correspondente. O protocolo deve ser fixado antes de examinar os acertos; não acrescentar questões sucessivamente até um intervalo passar de 95%.

A margem normal aproximada de pior caso para a proporção geral com n=30 e N=359 é ±{100*study['margem_normal_aproximada_pior_caso_com_correcao_finita']:.2f} pontos percentuais, com correção finita. É apenas indicação da baixa resolução; não usar aproximação normal para o intervalo próximo de 100%.

## Completude dos arquivos recebidos

JSON/CSV foram localizados na raiz de PIPILINE-GPT. A exportação registra 30 respostas e IDs corretos, mas apenas 1/30 concluída: 28 marcadas como classificadas não têm tema escolhido e há uma marcação de fora sem justificativa. O usuário informou que verificará com o avaliador. Isso é uma pendência da coleta/exportação, independente da validade do sorteio. Não transformar ausências em acertos, erros ou abstenções do modelo.

## Procedimento recomendado

1. Preservar este sorteio, seus arquivos e a política de publicação congelada.
2. Obter a exportação completa e confirmar exposição prévia do avaliador.
3. Comparar as publicadas com a nova referência, reportando n avaliável, acerto exato, acerto por ramo e incerteza; tratar revisar separadamente.
4. Usar os 30 como auditoria inicial, sem proclamar certificação de 95%.
5. Se for necessária evidência mais forte, definir antes dos resultados um plano adicional com tamanho, alvo e regra de parada fixos. Amostragem estratificada pode melhorar cobertura de disciplinas; revisar as exclusões deve ser outra componente identificada.

## Referências

- Statistics Canada, [Probability sampling](https://www150.statcan.gc.ca/n1/edu/power-pouvoir/ch13/prob/5214899-eng.htm): seleção probabilística, amostragem simples e cobertura de subgrupos.
- NIST, [Exact binomial confidence limits](https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbici.htm): intervalos exatos e cautela com amostras pequenas/raridade de falhas.
- Os cálculos do lote finito usam P(X=0)=C(N-D,n)/C(N,n), distribuição hipergeométrica. Script e contagens estão ao lado deste relatório.
'''
    (OUT/'REPRESENTATIVIDADE.md').write_text(report,encoding='utf-8')
    print(json.dumps({'sorteio_valido':True,'publicadas_na_amostra':np,'comparacao_de_acertos_realizada':False,'relatorio':str(OUT/'REPRESENTATIVIDADE.md'),'completude':exports},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
