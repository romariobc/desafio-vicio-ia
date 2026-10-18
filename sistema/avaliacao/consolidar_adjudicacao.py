"""Consolida a adjudicação humana sem alterar modelo, previsão ou avaliação cega."""
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

BASE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(BASE))
from pipeline import mesmo_ramo,wilson

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ler(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def salvar(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csv_salvar(p,rows):
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    files=list(BASE.glob('adjudicacao_v2_*.json'));assert len(files)==1,'Especifique uma única versão de adjudicação'
    jf=files[0];cf=jf.with_suffix('.csv');d=json.loads(jf.read_text(encoding='utf-8-sig'))
    frozen=Path(__file__).resolve().parent/'resultado_9b59368aa29f/revisao_humana_recebida.json'
    blind=json.loads(frozen.read_text(encoding='utf-8-sig'))
    assert d['registro_experimento']['base_avaliacao_sha256']==sha(frozen)
    assert d['respostas_originais_30']==blind['respostas'],'Respostas anteriores foram modificadas'
    assert d.get('avaliador','').strip(),'Autoria ausente'
    model_path=BASE/'publicacao.csv';forecast_path=BASE/'previsao.txt'
    original_hashes={p.name:sha(p) for p in [model_path,forecast_path]}
    manifest=json.loads((BASE/'manifesto_execucao.json').read_text(encoding='utf-8'))
    assert sha(model_path)==manifest['arquivos_sha256']['publicacao.csv']
    assert sha(model_path)==d['registro_experimento']['modelo_congelado_sha256']
    assert sha(forecast_path)==manifest['arquivos_sha256']['previsao.txt']
    temas={r['tema_id']:r for r in ler(BASE/'dados/temas_ativos.csv')}
    modelo={r['id']:r for r in ler(model_path)}
    prev={r['id']:r for r in blind['respostas']}
    divergencias={h['id'] for h in blind['respostas'] if not mesmo_ramo(modelo[h['id']]['tema_central_id'] or 'fora',h['tema_referencia_id'],temas)}
    adj=d['adjudicacoes'];assert len(adj)==len({r['id'] for r in adj})==15
    assert {r['id'] for r in adj}==divergencias
    cr=ler(cf);assert len(cr)==15
    for a,c in zip(adj,cr):
        for field in ['id','tema_humano_anterior','tema_modelo','escolha','situacao_final','tema_referencia_id','explicacao','conceito','evidencia']:
            assert a.get(field,'')==c.get(field,''),('JSON/CSV divergem',a['id'],field)
        assert a['concluida'] is True and c['concluida']=='true'
        assert a.get('motivos') or a.get('explicacao','').strip()
        assert a['tema_humano_anterior']==prev[a['id']]['tema_referencia_id']
        assert a['tema_modelo']==(modelo[a['id']]['tema_central_id'] or 'fora')
        if a['situacao_final']=='classificada':assert a['tema_referencia_id'] in temas
        elif a['situacao_final']=='fora':assert a['tema_referencia_id']=='fora'
        elif a['situacao_final']=='indeterminada':assert not a['tema_referencia_id']
        else:raise ValueError('Adjudicação pendente')
        if a['escolha']=='adotar_modelo':assert a['tema_referencia_id']==a['tema_modelo']
        if a['escolha']=='manter_anterior':assert a['tema_referencia_id']==a['tema_humano_anterior']
    byadj={a['id']:a for a in adj};pairs=[]
    for h in blind['respostas']:
        qid=h['id'];a=byadj.get(qid);m=modelo[qid];pred=m['tema_central_id'] or 'fora';old=h['tema_referencia_id']
        gold=a['tema_referencia_id'] if a else old
        pairs.append({'id':qid,'decisao_modelo':m['decisao'],'tema_modelo':pred,
            'caminho_modelo':temas[pred]['caminho'] if pred in temas else pred,
            'tema_humano_cega':old,'tema_humano_adjudicado':gold,
            'caminho_humano_adjudicado':temas[gold]['caminho'] if gold in temas else gold,
            'passou_por_adjudicacao':bool(a),'escolha_adjudicacao':a['escolha'] if a else '',
            'acerto_ramo_cega':mesmo_ramo(pred,old,temas),'acerto_exato_cega':pred==old,
            'acerto_ramo_adjudicada':mesmo_ramo(pred,gold,temas) if gold else None,
            'acerto_exato_adjudicada':pred==gold if gold else None,
            'confianca_modelo':float(m['confianca']),
            'motivos_adjudicacao':'; '.join(a['motivos']) if a else '',
            'explicacao_adjudicacao':a.get('explicacao','') if a else ''})
    def stats(items,stage):
        valid=[r for r in items if r['acerto_ramo_'+stage] is not None];n=len(valid);k=sum(r['acerto_ramo_'+stage] for r in valid)
        return {'n_avaliavel':n,'acertos_ramo':k,'acertos_exatos':sum(r['acerto_exato_'+stage] for r in valid),
            'concordancia_ramo':k/n if n else None,'wilson_95_descritivo':wilson(k,n),
            'brier':sum((r['confianca_modelo']-r['acerto_ramo_'+stage])**2 for r in valid)/n if n else None}
    pub=[r for r in pairs if r['decisao_modelo']=='publicar']
    before=stats(pub,'cega');after=stats(pub,'adjudicada')
    prediction=float(forecast_path.read_text(encoding='utf-8').splitlines()[0].split(':')[1])
    remaining=[r for r in pairs if r['acerto_ramo_adjudicada'] is False]
    out=Path(__file__).resolve().parent/('adjudicacao_'+sha(jf)[:12]);out.mkdir(exist_ok=True)
    (out/'adjudicacao_recebida.json').write_bytes(jf.read_bytes());(out/'adjudicacao_recebida.csv').write_bytes(cf.read_bytes())
    result={'validacao':{'adjudicacoes':len(adj),'concluidas':15,'autoria_preenchida':True,
        'csv_json_coerentes':True,'originais_cegos_preservados':True,'modelo_e_previsao_preservados':True},
        'escolhas':dict(Counter(a['escolha'] for a in adj)),
        'cega':{'total':stats(pairs,'cega'),'publicadas':before},
        'adjudicada':{'total':stats(pairs,'adjudicada'),'publicadas':after},
        'divergencias_remanescentes':remaining,
        'previsao_original':prediction,
        'diferenca_observado_adjudicado_menos_previsto_pp':100*(after['concordancia_ramo']-prediction),
        'meta_pontual_na_referencia_adjudicada':after['concordancia_ramo']>=.95,
        'precisao_minima_95_comprovada':False,'novo_teste_independente':False,
        'fontes':{'adjudicacao_json_sha256':sha(jf),'adjudicacao_csv_sha256':sha(cf),
            'avaliacao_cega_sha256':sha(frozen),'modelo_sha256':sha(model_path),'previsao_sha256':sha(forecast_path),
            'exportado_em':d.get('exportado_em')},
        'limites':['Adjudicação mostrou as propostas do modelo; risco de ancoragem.',
            'A amostra possui só 26 publicadas e composição desigual.',
            'Justificativas em categorias curtas, sem explicações livres; Q0058 marca mais específico e mais abrangente.',
            'Nenhuma correção da referência foi feita pelo assistente; todos os rótulos finais vieram do avaliador.',
            'Não reinterpretar a etapa cega como se tivesse obtido 96,15%.']}
    salvar(out/'metricas_adjudicacao.json',result);csv_salvar(out/'comparacao_30_antes_depois.csv',pairs)
    reference=[]
    for r in pairs:
        reference.append({'id':r['id'],'tema_referencia_id':r['tema_humano_adjudicado'],
            'situacao':'classificada' if r['tema_humano_adjudicado'] in temas else ('fora' if r['tema_humano_adjudicado']=='fora' else 'indeterminada'),
            'origem':'adjudicacao_assistida_v2' if r['passou_por_adjudicacao'] else 'avaliacao_cega_original',
            'motivos':r['motivos_adjudicacao'],'explicacao':r['explicacao_adjudicacao']})
    csv_salvar(out/'referencia_30_adjudicada.csv',reference)
    ci=after['wilson_95_descritivo']
    report=f'''# Consolidação da conferência humana — versão 2

## Integridade

15/15 divergências conferidas, autoria preenchida, justificativas registradas e CSV/JSON coerentes. As respostas cegas embutidas conferem com a versão recebida antes da adjudicação. A classificação e a previsão originais mantêm seus hashes. A exportação ocorreu em {d.get('exportado_em')} (UTC).

## Decisões do avaliador

- Adotou a proposta do modelo em 14 casos.
- Manteve a escolha anterior em Q0205 (Carta Testemunhável, ID 5567).
- Nenhum caso ficou indeterminado.
- A versão 2 apresentou as duas propostas; portanto é adjudicação assistida, não avaliação cega independente.

## Resultados preservados lado a lado

| Medida | Etapa cega original | Depois da adjudicação |
|---|---:|---:|
| Acerto por ramo nas publicadas | 14/26 (53,85%) | 25/26 (96,15%) |
| Acerto exato nas publicadas | 11/26 (42,31%) | 22/26 (84,62%) |
| Acerto por ramo nas 30 | 15/30 (50,00%) | 29/30 (96,67%) |
| Acerto exato nas 30 | 11/30 (36,67%) | 25/30 (83,33%) |

O modelo permaneceu igual: a mudança vem da conferência dos rótulos de referência pelo avaliador. Não é melhoria obtida por reclassificação automática nem um segundo teste independente com 96,15% de acerto.

A meta pontual de 95% é atingida em relação à referência adjudicada. O intervalo Wilson descritivo nas publicadas é {100*ci[0]:.2f}%–{100*ci[1]:.2f}%; seu limite inferior continua abaixo de 95%. Tamanho da amostra, composição, exposição anterior e ancoragem impedem alegar comprovação da precisão mínima no lote ou gabarito oficial.

## Previsão

A previsão original permanece {prediction*100:.2f}%. A concordância por ramo adjudicada é {100*after['concordancia_ramo']:.2f}%, diferença de {100*(after['concordancia_ramo']-prediction):.2f} ponto percentual acima da previsão. A proximidade é descritiva: rótulos foram conferidos após mostrar as propostas e não constituem validação independente da calibração.

## Divergência remanescente

Q0205: o modelo sugeriu Parte Geral dos Recursos (5512), enquanto o avaliador manteve Carta Testemunhável (5567). Na árvore, 5512 e 5567 pertencem a ramos distintos: 5567 descende de Recursos em Espécies (5560). Por isso é erro pela regra do desafio, mesmo ambos se referindo a recursos. Extras não alteram essa avaliação. Não corrigimos a classificação congelada após o resultado.

## Limites das justificativas

Os motivos selecionados foram registrados pelo avaliador. Não foram acrescentadas explicações livres. Em Q0058 foram marcados simultaneamente Tema mais específico e Tema mais abrangente, o que merece esclarecimento se usado para defender o critério. Isso não modifica automaticamente o rótulo final. Eventuais esclarecimentos devem gerar nova versão identificada.

## Uso no case

Apresentar os dois resultados e explicar a mudança na referência. A referência adjudicada é uma base operacional para desenvolvimento, com risco de ancoragem documentado. Se usada para ajustar o classificador ou o corte, a avaliação seguinte precisa de uma amostra separada e protocolo definido antes dos resultados. Não substituir silenciosamente o teste cego por esta etapa assistida.

Arquivos nesta pasta: exportações recebidas, referência consolidada das 30, comparação antes/depois e métricas. Nenhum arquivo da classificação, previsão ou primeira avaliação foi sobrescrito.
'''
    (out/'CONSOLIDACAO.md').write_text(report,encoding='utf-8')
    assert original_hashes=={p.name:sha(p) for p in [model_path,forecast_path]}
    print(json.dumps({'pasta':str(out),'escolhas':result['escolhas'],'publicadas_antes':before,'publicadas_depois':after,
        'remanescentes':[r['id'] for r in remaining],'diferenca_previsao_pp':result['diferenca_observado_adjudicado_menos_previsto_pp']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
