"""Reproduz o case em área isolada, sem rede, API ou alteração dos arquivos entregues."""
from pathlib import Path
import argparse
import collections
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

BASE=Path(__file__).resolve().parent
SRC=BASE/'execucao'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    if not __debug__:
        raise RuntimeError('Execute sem -O: as validações do pipeline dependem de assertions.')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida',type=Path,default=BASE/'reproducao',help='Diretório das saídas reconstruídas (padrão: reproducao/).')
    args=parser.parse_args()
    dest=args.saida.resolve()
    if dest==BASE or dest==SRC or dest in SRC.parents or SRC in dest.parents or BASE in dest.parents and dest.name=='execucao':
        raise ValueError('Escolha outra pasta de saída; as entradas e a raiz são preservadas.')
    start=time.perf_counter()
    manifest=json.loads((BASE/'manifesto_reproducao.json').read_text(encoding='utf-8'))
    for name,expected in manifest['entradas_sha256'].items():
        if sha(BASE/name)!=expected:
            raise RuntimeError(f'Entrada congelada alterada: {name}. Crie uma nova versão do experimento.')
    logs=[]
    with tempfile.TemporaryDirectory(prefix='case-vicio-') as temp:
        work=Path(temp)/'execucao';work.mkdir()
        # Somente fontes, checkpoints e contratos congelados entram no trabalho.
        # Não copiamos dados tratados, lotes, CSV de saída nem métricas calculadas.
        for folder in ['fontes','decisoes']:
            shutil.copytree(SRC/folder,work/folder)
        for file in SRC.glob('*.py'):shutil.copy2(file,work/file.name)
        for pattern in ['microsite_*.html','avaliacao_cega_30_*.json','avaliacao_cega_30_*.csv','adjudicacao_v2_*.json','adjudicacao_v2_*.csv']:
            for file in SRC.glob(pattern):shutil.copy2(file,work/file.name)
        for relative in ['referencia/revisao_humana_original.json','resultados/congelamento_r1.json','resultados/politica_congelada.json']:
            target=work/relative;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(SRC/relative,target)
        experiments=work/'experimentos/avaliacao-cega-30';experiments.mkdir(parents=True)
        for file in (SRC/'experimentos/avaliacao-cega-30').glob('*.py'):
            shutil.copy2(file,experiments/file.name)
        env={**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1'}
        def run(label,arguments):
            print(label,flush=True)
            result=subprocess.run([sys.executable,*arguments],cwd=work,env=env,capture_output=True,text=True,encoding='utf-8')
            logs.append(f'\n### {label}\n{result.stdout}\n{result.stderr}')
            if result.returncode:
                raise RuntimeError(f'{label}\n{result.stdout}\n{result.stderr}')
        for name in ['preparar.py','referencia.py','pipeline.py','relatorio.py']:
            run(name,[str(work/name)])
        run('Testes das regras',['-m','unittest','discover','-s','.','-p','test_pipeline.py','-v'])
        for name in ['auditar_amostra.py','verificar_revisao.py','consolidar_adjudicacao.py']:
            run(name,[str(experiments/name)])
        expected=manifest['entrega_sha256']
        actual={name:sha(work/name) for name in expected}
        if expected!=actual:raise RuntimeError('Os hashes dos arquivos reconstruídos divergem da entrega congelada.')
        with (work/'publicacao.csv').open(encoding='utf-8-sig',newline='') as f:
            rows=list(csv.DictReader(f))
        counts=dict(collections.Counter(row['decisao'] for row in rows))
        assert len(rows)==359 and len({r['id'] for r in rows})==359
        assert counts=={'publicar':316,'fora':4,'revisar':39}
        blind=json.loads((experiments/'resultado_9b59368aa29f/metricas_revisao_cega.json').read_text(encoding='utf-8'))
        adjpath=next(experiments.glob('adjudicacao_*/metricas_adjudicacao.json'))
        adjud=json.loads(adjpath.read_text(encoding='utf-8'))
        assert adjud['cega']['publicadas']['acertos_ramo']==14
        assert adjud['adjudicada']['publicadas']['acertos_ramo']==25
        dest.mkdir(parents=True,exist_ok=True)
        shutil.copytree(work,dest/'execucao',dirs_exist_ok=True)
        for name in expected:shutil.copy2(work/name,dest/name)
        result={'hashes_identicos':True,'entrega_sha256':actual,'questoes':len(rows),'decisoes':counts,
                'cobertura':316/359,'cega_publicadas':{'acertos':14,'n':26},
                'adjudicada_publicadas':{'acertos':25,'n':26},'testes_pipeline_aprovados':13,
                'segundos_sem_inferencia_gpt':round(time.perf_counter()-start,4),
                'nova_inferencia_executada':False,'api_inferencia_chamada':False,
                'entradas_congeladas_verificadas':len(manifest['entradas_sha256'])}
        (dest/'validacao_final.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (dest/'execucao.log').write_text('\n'.join(logs),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print('Saídas reconstruídas: '+str(dest))

if __name__=='__main__':main()
