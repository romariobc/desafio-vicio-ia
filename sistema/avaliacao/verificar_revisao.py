"""Valida a exportação e avalia a política congelada, sem retunar nem adjudicar."""
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

BASE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(BASE))
from pipeline import mesmo_ramo,wilson

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csv_ler(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def guardar(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    files=list(BASE.glob('avaliacao_cega_30_*.json'))
    assert len(files)==1,'Escolha explicitamente uma exportação se houver múltiplas versões.'
    jf=files[0];cf=jf.with_suffix('.csv')
    data=json.loads(jf.read_text(encoding='utf-8-sig'));human=data['respostas']
    site=(BASE/'microsite_avaliacao_cega_30.html').read_text(encoding='utf-8')
    sample=json.loads(re.search(r'<script id="experimento" type="application/json">(.*?)</script>',site,re.S).group(1))
    rows=csv_ler(BASE/'publicacao.csv');modelo={r['id']:r for r in rows}
    temas={t['tema_id']:t for t in csv_ler(BASE/'dados/temas_ativos.csv')}
    manifest=json.loads((BASE/'manifesto_execucao.json').read_text(encoding='utf-8'))
    assert sha(BASE/'publicacao.csv')==manifest['arquivos_sha256']['publicacao.csv'],'Classificação do modelo mudou'
    assert len(human)==len({r['id'] for r in human})==30
    assert {r['id'] for r in human}=={r['id'] for r in sample['questoes']}
    assert data['registro_experimento']==sample['registro']
    csv_rows=csv_ler(cf)
    assert [(r['id'],r['situacao'],r['tema_referencia_id']) for r in human]==[(r['id'],r['situacao'],r['tema_referencia_id']) for r in csv_rows]
    for h in human:
        assert h.get('concluida') is True,('Resposta incompleta',h['id'])
        assert h['situacao'] in ('classificada','fora','indeterminada')
        if h['situacao']=='classificada':assert h['tema_referencia_id'] in temas
        if h['situacao']=='fora':assert h['tema_referencia_id']=='fora' and h.get('observacao','').strip()
    out=Path(__file__).resolve().parent/('resultado_'+sha(jf)[:12])
    out.mkdir(exist_ok=True)
    (out/'revisao_humana_recebida.json').write_bytes(jf.read_bytes())
    (out/'revisao_humana_recebida.csv').write_bytes(cf.read_bytes())
    pairs=[]
    for h in human:
        m=modelo[h['id']];a=m['tema_central_id'] or 'fora';g=h['tema_referencia_id'];evaluable=h['situacao']!='indeterminada'
        pairs.append({'id':h['id'],'decisao_modelo':m['decisao'],'tema_modelo':a,
            'caminho_modelo':temas[a]['caminho'] if a in temas else 'fora',
            'tema_humano':g,'caminho_humano':temas[g]['caminho'] if g in temas else g,
            'acerto_ramo':mesmo_ramo(a,g,temas) if evaluable else None,
            'acerto_exato':a==g if evaluable else None,'confianca_modelo':float(m['confianca']),
            'observacao_revisor':h.get('observacao',''),'exposicao_previa':h.get('exposicao_previa','nao_informado')})
    def stats(ps):
        valid=[p for p in ps if p['acerto_ramo'] is not None];n=len(valid);k=sum(p['acerto_ramo'] for p in valid)
        return {'selecionadas':len(ps),'avaliaveis':n,'acertos_ramo':k,'acertos_exatos':sum(p['acerto_exato'] for p in valid),
            'concordancia_ramo':k/n if n else None,'wilson_95_binomial_descritivo':wilson(k,n),
            'confianca_media_modelo':sum(p['confianca_modelo'] for p in valid)/n if n else None,
            'brier':sum((p['confianca_modelo']-p['acerto_ramo'])**2 for p in valid)/n if n else None}
    pub=stats([p for p in pairs if p['decisao_modelo']=='publicar']);total=stats(pairs)
    prediction=float((BASE/'previsao.txt').read_text(encoding='utf-8').splitlines()[0].split(':')[1])
    result={'estado':'Comparação bruta contra referência humana recebida, sem adjudicação',
        'validacao':{'respostas':len(human),'concluidas':30,'temas_ativos_validos':True,'mesmos_ids_sorteio':True,
            'csv_json_coerentes':True,'modelo_congelado_preservado':True,
            'revisor_identificado':bool(data.get('revisor',{}).get('identificacao','').strip()),
            'exposicao_previa':dict(Counter(h.get('exposicao_previa','nao_informado') for h in human))},
        'fontes':{'json_sha256':sha(jf),'csv_sha256':sha(cf),'modelo_sha256':sha(BASE/'publicacao.csv'),
            'exportado_em':data.get('exportado_em'),'experimento_id':data['registro_experimento']['experimento_id']},
        'todas':total,'publicadas':pub,'revisar':stats([p for p in pairs if p['decisao_modelo']=='revisar']),
        'meta_pontual_95_atingida':pub['concordancia_ramo'] is not None and pub['concordancia_ramo']>=.95,
        'previsao_original':prediction,'diferenca_previsao_menos_observado_pp':100*(prediction-pub['concordancia_ramo']) if pub['concordancia_ramo'] is not None else None,
        'cobertura_lote_congelado':sum(r['decisao']=='publicar' for r in rows)/len(rows),
        'acao':'Não alterar classificação nem calibrar usando esta avaliação. Eventuais adjudicações precisam de nova versão e justificativa externa.',
        'limitacoes':['Amostra pequena e desequilíbrio de disciplinas previamente documentados.','3 itens têm rótulos usados na calibração anterior.','Identificação do revisor e exposição prévia não informadas.','Referência humana recebida não é o gabarito oficial.','Concordância baixa não permite atribuir automaticamente toda divergência ao modelo ou ao revisor.']}
    guardar(out/'metricas_revisao_cega.json',result)
    with (out/'comparacao_30.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
    mismatches=[p for p in pairs if p['acerto_ramo'] is False]
    table=['| Questão | Decisão | Tema do modelo | Tema humano |','|---|---|---|---|']
    for p in mismatches:table.append(f"| {p['id']} | {p['decisao_modelo']} | {p['tema_modelo']} — {p['caminho_modelo']} | {p['tema_humano']} — {p['caminho_humano']} |")
    ci=pub['wilson_95_binomial_descritivo']
    report=f'''# Verificação da revisão cega refeita

## Integridade

30 respostas concluídas, IDs correspondentes ao sorteio original, temas ativos e consistência entre CSV/JSON. São 29 classificações na árvore e 1 fora com justificativa. O arquivo foi exportado em {data.get('exportado_em')} (UTC). A classificação congelada do modelo permaneceu íntegra.

Identificação do avaliador não preenchida; exposição prévia não informada nas 30 respostas. Portanto, cegamento da interface é verificável, mas experiência prévia e autoria não estão documentadas no arquivo. Os problemas de tamanho/composição da amostra permanecem descritos em ../REPRESENTATIVIDADE.md.

## Resultado bruto — regra de ancestralidade do desafio

| Subconjunto | Acertos por ramo | Acertos exatos |
|---|---:|---:|
| Todas as 30 | {total['acertos_ramo']}/30 ({total['concordancia_ramo']*100:.2f}%) | {total['acertos_exatos']}/30 |
| Publicadas | {pub['acertos_ramo']}/26 ({pub['concordancia_ramo']*100:.2f}%) | {pub['acertos_exatos']}/26 |
| Revisar | {result['revisar']['acertos_ramo']}/4 | {result['revisar']['acertos_exatos']}/4 |

As 12 divergências nas publicadas contam contra a referência recebida. Extras não corrigem central errado; irmãos e nós homônimos em ramos diferentes não são equivalentes. Nenhum ID foi remapeado automaticamente para melhorar o resultado.

Intervalo Wilson bilateral descritivo nas publicadas: {ci[0]*100:.2f}%–{ci[1]*100:.2f}%. A cobertura da entrega permanece 316/359 = {result['cobertura_lote_congelado']*100:.2f}%; cobertura não é precisão.

Previsão original: {prediction*100:.2f}%. Observado contra esta referência nas publicadas: {pub['concordancia_ramo']*100:.2f}%. Diferença: {result['diferenca_previsao_menos_observado_pp']:.2f} pontos percentuais. A meta pontual de 95% não foi atingida neste experimento. Esta evidência contradiz o desempenho sugerido pela referência antiga e precisa ser apresentada, não ocultada.

## Divergências que pedem adjudicação

Há escolhas de referência que suscitam dúvida semântica. Por exemplo, Q0239 apresenta alternativas sobre cálculo/dosimetria da pena, mas recebeu tema de teorias sociológicas da criminalidade; Q0100 trata de uma situação sexual com menor e recebeu Difamação. São sinais para conferir a seleção no formulário e os critérios jurídicos; não constituem prova de que o revisor errou. Outras diferenças envolvem foco da questão (conceito geral, tipo específico ou contexto do caso) e fronteiras da árvore.

Preservar os rótulos recebidos. Se o avaliador corrigir algum, obter ID, rótulo anterior, novo rótulo, justificativa e autoria em outra versão. Não usar a própria LLM como árbitro final para transformar suas discordâncias em acertos.

{chr(10).join(table)}

## Próximo passo

Conferir com o avaliador as divergências e preencher identificação/exposição prévia. Manter separadas a comparação original e eventual comparação adjudicada. Se houver novos ajustes do classificador usando estes resultados, esta amostra passa a integrar desenvolvimento; a próxima avaliação deverá ser outra amostra planejada antes dos resultados. Nenhum ajuste ou nova classificação foi executado nesta verificação.
'''
    (out/'RESULTADO.md').write_text(report,encoding='utf-8')
    print(json.dumps({'pasta':str(out),'integridade':result['validacao'],'publicadas':pub,
        'todas':total,'meta_atingida':result['meta_pontual_95_atingida'],'diferenca_previsao_pp':result['diferenca_previsao_menos_observado_pp']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
