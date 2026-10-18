"""Importação literal da referência anterior e partição; não altera a R1."""
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
from preparar import BASE, carregar, salvar_json, csv_gravar, sha

def main():
    _, temas = carregar()
    origem = BASE.parent/'PIPILINE/dados/revisao_humana.json'
    destino = BASE/'referencia/revisao_humana_original.json'
    destino.parent.mkdir(exist_ok=True)
    # A cópia recebida é entrada congelada desta execução. Reprodução da pasta
    # independe de existir a entrega antiga ao lado; não reimportar silenciosamente.
    if not destino.exists():destino.write_bytes(origem.read_bytes())
    respostas = json.loads(destino.read_text(encoding='utf-8'))['respostas']
    ref=[]
    for qid, r in sorted(respostas.items()):
        original=r['tema_ia_id'] or 'fora'
        assert original=='fora' or original in temas
        veredito=r['veredito']
        corrigido=r.get('tema_corrigido_id','').strip()
        if veredito=='concordo':
            tema=original; situacao='rotulo_positivo'
        elif veredito=='concordo_pai':
            assert original in temas and temas[original]['parent_id']
            tema=corrigido or r.get('tema_pai_id') or temas[original]['parent_id']
            assert tema in temas
            assert tema==temas[original]['parent_id'], 'Pai registrado diverge da taxonomia original'
            situacao='rotulo_positivo'
        elif veredito=='discordo':
            tema=corrigido
            situacao='rotulo_corrigido' if tema else 'restricao_negativa_sem_rotulo'
        else: raise ValueError(('veredito desconhecido',qid,veredito))
        assert not tema or tema=='fora' or tema in temas
        ref.append({'id':qid,'estrato_original':r['estrato'],'veredito':veredito,'sugestao_antiga':original,
                    'tema_referencia_id':tema,'situacao':situacao,'observacao':r.get('observacao',''),
                    'ancoragem_aceita':True,'origem':'revisao_humana_original.json'})
    rng=random.Random(20261018); grupos=defaultdict(list)
    for r in ref:grupos[(r['estrato_original'],r['veredito'])].append(r)
    for _,itens in sorted(grupos.items()):
        rng.shuffle(itens)
        # Ao menos uma observação de cada grupo (inclusive grupos unitários) vai
        # à calibração. O reservado não é um teste cego; isso está no plano.
        n_cal=max(1,round(len(itens)*2/3))
        for i,r in enumerate(itens):r['particao']='calibracao' if i<n_cal else 'avaliacao_reservada'
    ref.sort(key=lambda r:r['id'])
    csv_gravar(BASE/'referencia/referencia_normalizada.csv',ref,list(ref[0]))
    salvar_json(BASE/'referencia/particoes.json',{p:[r['id'] for r in ref if r['particao']==p] for p in ('calibracao','avaliacao_reservada')})
    salvar_json(BASE/'referencia/proveniencia.json',{
        'origem_local':str(origem),'sha256':sha(destino),'numero_revisoes':len(ref),
        'rotulos_positivos':sum(bool(r['tema_referencia_id']) for r in ref),
        'restricoes_negativas':[r['id'] for r in ref if not r['tema_referencia_id']],
        'risco_ancoragem_aceito_por_usuario':True,
        'motivo_aceitacao':'Prazo curto do desafio, otimização do tempo e experiência do revisor humano, conforme declaração do usuário.',
        'autoria_revisao':'Informada pelo usuário como revisão humana; identidade, credenciais e duração não verificadas pelo arquivo.',
        'selecao_original':'IDs dirigidos/fixos, probabilidades de inclusão desconhecidas',
        'particao_semente':20261018,'exposicao_historica':'A sessão já teve acesso a resultados e parte dos pareceres; avaliação reservada não é cega.',
        'precisao_oficial':'Não identificável sem os rótulos reservados da empresa.'})
    print('Referência importada:',len(ref),'itens; partições em referencia/particoes.json')

if __name__=='__main__':main()
