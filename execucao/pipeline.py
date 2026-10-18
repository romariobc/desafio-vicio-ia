"""Reproduz decisões GPT registradas, calibra na partição própria e avalia uma vez.

Não chama LLM. Inferência: leitura e registro pelo assistente da sessão Codex.
"""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from preparar import BASE, carregar, csv_gravar, csv_ler, salvar_json, sha

CAMPOS = ['id','decisao','tema_central_id','extras_ids','confianca','motivo']
CORTES = [.80,.85,.90,.95,.97,.98,.99,1.0]
BLOQUEIOS = {'mosaico','generico','texto_incompleto','texto_inconsistente','referencia_inconclusiva','lei_especial_sem_no'}

def psv(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='|'))

def ancestral(a,b,temas):
    while b:
        if a==b:return True
        b=temas[b]['parent_id']
    return False

def mesmo_ramo(a,b,temas):
    if a=='fora' or b=='fora':return a==b
    return a in temas and b in temas and (ancestral(a,b,temas) or ancestral(b,a,temas))

def wilson(k,n):
    if not n:return None
    z=1.96; p=k/n; den=1+z*z/n
    centro=(p+z*z/(2*n))/den; raio=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0,centro-raio),min(1,centro+raio)]

def bin_score(s):
    return 'baixo' if s<.8 else ('medio' if s<.95 else 'alto')

def validar(row,temas):
    assert row['decisao'] in ('publicar','revisar','fora')
    v=float(row['confianca']); assert math.isfinite(v) and 0<=v<=1
    central=row['tema_central_id']; extras=[e for e in row['extras_ids'].split(';') if e]
    assert len(extras)==len(set(extras)) and central not in extras
    assert all(e in temas for e in extras)
    if row['decisao']=='fora': assert not central and not extras
    else:assert central in temas
    assert row['motivo'].strip()

def ler_r1(qs,temas):
    file=BASE/'decisoes/r1.psv'
    frozen=json.loads((BASE/'resultados/congelamento_r1.json').read_text(encoding='utf-8'))
    assert sha(file)==frozen['sha256'], 'R1 mudou após congelamento'
    rows=psv(file); byq={q['id']:q for q in qs}
    assert len(rows)==len(byq)==len({r['id'] for r in rows}) and {r['id'] for r in rows}==set(byq)
    for r in rows:
        r['score_bruto']=float(r['score_bruto']);assert math.isfinite(r['score_bruto']) and 0<=r['score_bruto']<=1
        assert r['conceito'] and r['evidencia']
        q=byq[r['id']]; full=' '.join(' '.join([q['enunciado'],q['comando'],*q['alternativas'].values()]).split())
        assert r['evidencia'] in full, ('evidência não literal',r['id'],r['evidencia'])
        validar({**r,'decisao':'revisar' if r['tema_central_id'] else 'fora','confianca':r['score_bruto'],'motivo':r['conceito']},temas)
    return rows

def comparar(rows,refs,temas):
    porid={r['id']:r for r in rows};saida=[]
    for h in refs:
        r=porid[h['id']];pred=r['tema_central_id'] or 'fora';gold=h['tema_referencia_id']
        conhecido=bool(gold)
        y=int(mesmo_ramo(pred,gold,temas)) if conhecido else None
        rejeitado=not conhecido and pred==h['sugestao_antiga']
        saida.append({'id':h['id'],'particao':h['particao'],'veredito_original':h['veredito'],
            'predicao':pred,'referencia':gold,'referencia_completa':conhecido,
            'acerto_ramo':y,'acerto_exato':int(pred==gold) if conhecido else None,
            'repete_sugestao_rejeitada':rejeitado,'score_bruto':r.get('score_bruto'),
            'confianca':float(r.get('confianca',r.get('score_bruto',0))),'decisao':r.get('decisao','pendente')})
    return saida

def resumo_comparacao(pares):
    conhecidos=[p for p in pares if p['referencia_completa']]
    k=sum(p['acerto_ramo'] for p in conhecidos);n=len(conhecidos)
    probabilisticos=[p for p in conhecidos if p['predicao']!='fora']
    rejeicoes=sum(p['repete_sugestao_rejeitada'] for p in pares)
    return {'referencias_recebidas':len(pares),'referencias_completas':n,'referencias_inconclusivas':len(pares)-n,
        'acertos_ramo':k,'precisao_ramo':k/n if n else None,
        'acertos_exatos':sum(p['acerto_exato'] for p in conhecidos),
        'acerto_exato':sum(p['acerto_exato'] for p in conhecidos)/n if n else None,
        'wilson_95_condicional':wilson(k,n),
        'repeticoes_de_rotulo_rejeitado':rejeicoes,
        'n_avaliaveis_incluindo_rejeicoes':n+rejeicoes,
        'precisao_incluindo_rejeicoes_conhecidas':k/(n+rejeicoes) if n+rejeicoes else None,
        'desconhecidos_apos_rejeicoes':len(pares)-n-rejeicoes,
        'brier_central_n':len(probabilisticos),
        'brier_central':sum((float(p['confianca'])-p['acerto_ramo'])**2 for p in probabilisticos)/len(probabilisticos) if probabilisticos else None,
        'brier_exclui_predicoes_fora':'Sem tema central, a confiança do tema é zero por contrato; não é probabilidade de exclusão correta.'}

def metricas(rows,refs,temas):
    pares=comparar(rows,refs,temas)
    pub=[p for p in pares if p['decisao']=='publicar']
    n=len(rows);c=Counter(r['decisao'] for r in rows)
    return {'total_lote':n,'decisoes':dict(c),'cobertura':c['publicar']/n,
        'abstencao_total':(c['revisar']+c['fora'])/n,'fila_revisao':c['revisar']/n,'exclusao':c['fora']/n,
        'referencia_toda':resumo_comparacao(pares),'publicadas_na_referencia':resumo_comparacao(pub),
        'observacao':'Precisão restrita à referência dirigida e ancorada; não estima sem viés o gabarito oficial.'}

def aplicar_ajustes(r1,temas,qs):
    r3={r['id']:dict(r) for r in r1};ajustes=psv(BASE/'decisoes/ajustes_r3.psv')
    assert len(ajustes)==len({r['id'] for r in ajustes})
    for a in ajustes:
        assert a['id'] in r3 and a['justificativa']
        old=r3[a['id']]
        for k in ('tema_central_id','extras_ids','alertas'):old[k]=a[k]
        old['score_bruto']=float(a['score_bruto'])
        old['ajuste_r3']=a['justificativa']
    for r in r3.values():
        r.setdefault('ajuste_r3','Mantidos tema e score da R1 após revisão dos critérios; nenhum ajuste automático por mera presença de extras.')
        r['origem_inferencia']='GPT da sessão Codex; reanálise documentada'
    return list(r3.values()),ajustes

def ajustar_calibrador(rows,refs_cal,temas):
    assert all(h['particao']=='calibracao' for h in refs_cal)
    pairs=comparar(rows,refs_cal,temas); buckets={b:[] for b in ('baixo','medio','alto')}
    for p in pairs:
        if p['referencia_completa'] and p['predicao']!='fora':buckets[bin_score(p['score_bruto'])].append(p)
    out={}
    for b,ps in buckets.items():
        n=len(ps);k=sum(p['acerto_ramo'] for p in ps)
        out[b]={'n':n,'acertos':k,'taxa_observada':k/n if n else None,
                'probabilidade_beta_1_1':(k+1)/(n+2),'wilson_95_condicional':wilson(k,n),
                'ids_ajuste':[p['id'] for p in ps]}
    # Pool adjacent violators (PAVA) assegura que score maior não gere probabilidade
    # menor. Cada bin recebe pseudocontagens Beta(1,1); não há pesos 65/35 arbitrários.
    blocks=[]
    for b in ('baixo','medio','alto'):
        v=out[b];blocks.append({'bins':[b],'sucessos':v['acertos']+1,'total':v['n']+2})
        while len(blocks)>1 and blocks[-2]['sucessos']/blocks[-2]['total']>blocks[-1]['sucessos']/blocks[-1]['total']:
            right=blocks.pop();left=blocks.pop()
            blocks.append({'bins':left['bins']+right['bins'],'sucessos':left['sucessos']+right['sucessos'],'total':left['total']+right['total']})
    for block in blocks:
        for b in block['bins']:
            out[b]['probabilidade_calibrada']=block['sucessos']/block['total']
            out[b]['bins_agrupados_pava']=block['bins']
    return {'metodo':'Bins fixos + média posterior Beta(1,1) + PAVA monotônico; calibração exploratória',
            'limites':[0,.8,.95,1.0],'bins':out,'rotulos_usados':[h['id'] for h in refs_cal],
            'teste_usado_no_ajuste':False,'garantia_de_calibracao_fora_da_amostra':False}

def prob(r,cal):
    return cal['bins'][bin_score(r['score_bruto'])]['probabilidade_calibrada']

def elegivel(r):
    return bool(r['tema_central_id']) and not (set(r['alertas'].split(';')) & BLOQUEIOS)

def decidir(rows,cut,cal=None):
    out=[]
    for r in rows:
        if not r['tema_central_id']:d='fora'
        elif elegivel(r) and cut is not None and r['score_bruto']>=cut:d='publicar'
        else:d='revisar'
        conf=0.0 if d=='fora' else (prob(r,cal) if cal else r['score_bruto'])
        bloqueados=sorted(set(r['alertas'].split(';')) & BLOQUEIOS)
        motivo=r.get('ajuste_r3',r['conceito'])
        if d=='revisar':motivo=f"Revisar: {', '.join(bloqueados) if bloqueados else 'abaixo do corte'}; "+motivo
        if d=='fora':motivo='Lacuna na taxonomia: '+r['conceito']
        out.append({**r,'decisao':d,'confianca':round(conf,6),'motivo':motivo})
    return out

def selecionar_politica(rows,refs_cal,temas,cal):
    assert all(h['particao']=='calibracao' for h in refs_cal), 'Não usar avaliação reservada para selecionar política'
    curve=[]
    for cut in CORTES:
        out=decidir(rows,cut,cal);m=metricas(out,refs_cal,temas);p=m['publicadas_na_referencia']
        publicadas=[r for r in out if r['decisao']=='publicar']
        expected=sum(r['confianca'] for r in publicadas)/len(publicadas) if publicadas else None
        # Erros negativos sem gabarito são bloqueados pela política e não viram acertos.
        acceptable=(p['referencias_completas']>=8 and p['precisao_ramo']>=.95
                    and p['referencias_inconclusivas']==0)
        curve.append({'corte':cut,'publicadas':len(publicadas),'cobertura':m['cobertura'],
            'calibracao_n':p['referencias_completas'],'calibracao_acertos':p['acertos_ramo'],
            'precisao_empirica_calibracao':p['precisao_ramo'],'wilson_95_condicional':p['wilson_95_condicional'],
            'media_confianca_calibrada':expected,'atinge_criterio_empirico':acceptable})
    options=[c for c in curve if c['atinge_criterio_empirico']]
    best=max(options,key=lambda c:(c['publicadas'],c['corte'])) if options else None
    return {'corte_escolhido':best['corte'] if best else None,'meta_pontual':.95,'minimo_referencias':8,
        'criterio':'Maximizar publicadas respeitando precisão empírica >=95% na calibração, mínimo 8 rótulos; alertas bloqueiam publicação.',
        'garante_meta_oficial':False,'curva':curve,'escolha':best,
        'momento_congelamento':'Antes de calcular métricas da partição reservada',
        'avaliacao_reservada_usada_na_escolha':False}

def exportar_rodada(name,rows,temas):
    for r in rows:validar(r,temas)
    pasta=BASE/'resultados'/name
    csv_gravar(pasta/'publicacao.csv',[{k:r[k] for k in CAMPOS} for r in rows],CAMPOS)
    (pasta/'decisoes_completas.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')

def escrever_arvore(qs,temas,rows):
    porid={r['id']:r for r in rows}; por_no=defaultdict(list)
    for q in qs:
        r=porid[q['id']];por_no[r['tema_central_id'] or 'fora'].append({'questao':q,'classificacao':r})
    def node(t):
        return {**t,'questoes':por_no[t['tema_id']], 'filhos':[node(f) for f in temas.values() if f['parent_id']==t['tema_id']]}
    salvar_json(BASE/'resultados/arvore_classificada.json',{'arvore':[node(t) for t in temas.values() if not t['parent_id']], 'fora':por_no['fora']})

def escrever_previsao(policy,rows,total):
    best=policy['escolha'];pub=[r for r in rows if r['decisao']=='publicar']
    point=sum(r['confianca'] for r in pub)/len(pub) if pub else None
    intervalo=best['wilson_95_condicional'] if best else [0,1]
    cobertura=len(pub)/total
    forecast=(f'precisao_prevista: {point or 0:.4f}\nprecisao_intervalo: {intervalo[0]:.4f}-{intervalo[1]:.4f}\n'
        f'cobertura_prevista: {cobertura:.4f}\ncobertura_intervalo: {cobertura:.4f}-{cobertura:.4f}\n\n'
        'Previsão pontual = média das probabilidades obtidas com referência de calibração, bins fixos, prior Beta(1,1) e PAVA. '
        'Intervalo Wilson calculado sobre acertos das publicadas na CALIBRAÇÃO; é descritivo e otimista após seleção de corte, '
        'não intervalo válido de generalização. A seleção original é dirigida e a revisão ancorada, riscos aceitos pelo usuário. '
        'A referência não é o gabarito oficial. Se não há publicadas, precisão é indefinida e zero é sentinela do formato.\n'
        'Cobertura é exata neste lote de 359, não previsão para novos lotes. Abstenção = revisar + fora. '
        'Resultados da partição reservada estão separados em resultados/metricas.json; não foram usados para escolher o corte.\n')
    # Preserva os bytes da previsão congelada também em Linux/macOS.
    (BASE/'previsao.txt').write_bytes(forecast.replace('\n','\r\n').encode('utf-8'))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--etapa',choices=['calibracao','completo'],default='completo')
    args=parser.parse_args()
    qs,temas=carregar();r1=ler_r1(qs,temas)
    refs=csv_ler(BASE/'referencia/referencia_normalizada.csv')
    assert len(refs)==60 and len({r['id'] for r in refs})==60
    refs_cal=[h for h in refs if h['particao']=='calibracao']
    r1out=decidir(r1,.95);exportar_rodada('r1',r1out,temas)
    r1compar=comparar(r1out,refs_cal,temas)
    csv_gravar(BASE/'resultados/r2/comparacao_r1_calibracao.csv',r1compar,list(r1compar[0]))
    r3,ajustes=aplicar_ajustes(r1,temas,qs)
    cal=ajustar_calibrador(r3,refs_cal,temas)
    salvar_json(BASE/'resultados/r2/calibrador.json',cal)
    policy=selecionar_politica(r3,refs_cal,temas,cal)
    # O hash da política/entradas não inclui timestamps para permitir reprodução.
    frozen={'politica':policy,'r1_sha256':sha(BASE/'decisoes/r1.psv'),
            'ajustes_r3_sha256':sha(BASE/'decisoes/ajustes_r3.psv'),
            'referencia_sha256':sha(BASE/'referencia/referencia_normalizada.csv')}
    path=BASE/'resultados/politica_congelada.json'
    if path.exists():assert json.loads(path.read_text(encoding='utf-8'))==frozen,'Política/entradas mudaram após congelamento: use nova versão, não sobrescreva o teste.'
    else:salvar_json(path,frozen)
    r3out=decidir(r3,policy['corte_escolhido'],cal);exportar_rodada('r3',r3out,temas)
    comparar_cal={'r1':metricas(r1out,refs_cal,temas),'r3':metricas(r3out,refs_cal,temas)}
    salvar_json(BASE/'resultados/r2/metricas_calibracao.json',comparar_cal)
    escrever_previsao(policy,r3out,len(qs))
    print('Política congelada:',policy['corte_escolhido'],'decisões',dict(Counter(r['decisao'] for r in r3out)))
    if args.etapa=='calibracao':return
    # A avaliação reservada só é consumida para métricas depois do congelamento.
    refs_test=[h for h in refs if h['particao']=='avaliacao_reservada']
    final={
        'calibracao':comparar_cal,
        'avaliacao_reservada':{'r1':metricas(r1out,refs_test,temas),'r3':metricas(r3out,refs_test,temas)},
        'referencia_completa_descritiva':{'r1':metricas(r1out,refs,temas),'r3':metricas(r3out,refs,temas)},
        'r1_e_r3_concordancia':sum(a['tema_central_id']==b['tema_central_id'] for a,b in zip(r1out,r3out))/len(qs),
        'alteracoes_semanticas':len(ajustes),
        'r3_vs_r1_temas_alterados':sum(a['tema_central_id']!=b['tema_central_id'] for a,b in zip(r1out,r3out)),
        'meta_oficial_comprovada':False,
        'risco_ancoragem_aceito':True,'selecao_referencia_probabilistica':False,
        'avaliacao_correcoes_calibracao_nao_e_generalizacao':True,
    }
    test=final['avaliacao_reservada']['r3']['publicadas_na_referencia']
    final['meta_pontual_referencia_reservada']=test['precisao_ramo'] is not None and test['precisao_ramo']>=.95
    final['limite_inferior_wilson_reservado_ge_95']=bool(test['wilson_95_condicional'] and test['wilson_95_condicional'][0]>=.95)
    salvar_json(BASE/'resultados/metricas.json',final)
    todos_pares=comparar(r3out,refs,temas)
    csv_gravar(BASE/'resultados/comparacao_referencia_r3.csv',todos_pares,list(todos_pares[0]))
    csv_gravar(BASE/'publicacao.csv',[{k:r[k] for k in CAMPOS} for r in r3out],CAMPOS)
    escrever_arvore(qs,temas,r3out)
    # Receita e saídas assinadas. Arquivos da entrega antiga não são escritos.
    targets=[p for p in BASE.rglob('*') if p.is_file() and '__pycache__' not in p.parts
             and p.name not in ('manifesto_execucao.json',) and p.suffix not in ('.pyc',)]
    salvar_json(BASE/'manifesto_execucao.json',{'origem_modelo':'Assistente GPT da sessão Codex; identificador comercial exato não confirmado',
        'api_externa_chamada':False,'tokens_faturados':None,'custo_marginal_usd':None,
        'custo':'Assinatura do ambiente; não há medição monetária por questão. Scripts locais não chamam API.',
        'inferencia_reproduzivel':'Os registros GPT são checkpoints de inferência; reexecução dos scripts reproduz pós-processamento e métricas, não nova inferência.',
        'r1_frozen':json.loads((BASE/'resultados/congelamento_r1.json').read_text(encoding='utf-8')),
        'fontes_github':json.loads((BASE/'fontes/proveniencia.json').read_text(encoding='utf-8')),
        'arquivos_sha256':{str(p.relative_to(BASE)).replace('\\','/'):sha(p) for p in sorted(targets)},
        'consistencia':{'lote':359,'ids_unicos':len({r['id'] for r in r3out}),'temas_ativos':len(temas)},
        'limitacao_tempo':'Duração isolada da inferência e tokens não instrumentados; não estimar como se medidos.'})
    print('Avaliação reservada:',json.dumps(test,ensure_ascii=False))

if __name__=='__main__':main()
