"""Reconstitui o experimento a partir de entradas versionadas, sem nova inferência."""
from pathlib import Path, PurePosixPath
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
import zipfile
from .previsao import explicar_previsao

BASE=Path(__file__).resolve().parents[1]
PROTEGIDOS=['sistema','dados','interfaces','experimentos','auditoria','testes','docs','.github','.git']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def validar_saida(dest):
    dest=dest.resolve()
    if dest==BASE or dest in BASE.parents:
        raise ValueError('A saída não pode substituir a raiz nem seus diretórios ancestrais.')
    for folder in PROTEGIDOS:
        source=(BASE/folder).resolve()
        if dest==source or source in dest.parents:
            raise ValueError(f'Use outra pasta de saída; {folder}/ contém arquivos versionados.')
    # Ao executar dentro de codigo/, também preservo os metadados do Git
    # que ficam no nível acima. A pasta codigo continua copiável isoladamente.
    for name in ['.git','.github']:
        admin=(BASE.parent/name).resolve()
        if admin.exists() and (dest==admin or admin in dest.parents):
            raise ValueError('A saída não pode ser gravada nos metadados do repositório.')
    return dest

def executar(label,args,cwd,logs):
    print(label,flush=True)
    env={**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1'}
    result=subprocess.run([sys.executable,*args],cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8')
    logs.append(f'\n### {label}\n{result.stdout}\n{result.stderr}')
    if result.returncode:raise RuntimeError(f'{label}\n{result.stdout}\n{result.stderr}')

def main():
    if not __debug__:raise RuntimeError('Execute sem -O: as regras usam assertions.')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida',type=Path,default=BASE/'saidas',help='Pasta das saídas reconstruídas (padrão: saidas/).')
    args=parser.parse_args();dest=validar_saida(args.saida)
    start=time.perf_counter()
    manifest=json.loads((BASE/'auditoria/manifesto_reproducao.json').read_text(encoding='utf-8'))
    for name,expected in manifest['entradas_sha256'].items():
        if sha(BASE/name)!=expected:raise RuntimeError(f'Entrada congelada alterada: {name}. Crie nova versão do experimento.')
    mapping=json.loads((BASE/'sistema/mapa_reproducao.json').read_text(encoding='utf-8'))
    logs=[]
    executar('Testes da organização',['-m','unittest','discover','-s','testes','-p','test_organizacao.py','-v'],BASE,logs)
    with tempfile.TemporaryDirectory(prefix='case-vicio-') as temp:
        # Windows pode fornecer TEMP com nome curto 8.3 (RUNNER~1).
        # Compare caminhos canônicos, sem relaxar a proteção de diretórios.
        work=(Path(temp)/'execucao').resolve();work.mkdir()
        # Os scripts originais conservam o layout que utilizaram no experimento.
        # O mapa só o monta temporariamente; nenhuma saída pronta é usada.
        for item in mapping['arquivos']:
            source=(BASE/item['origem']).resolve();target=(work/item['destino']).resolve()
            if not source.is_relative_to(BASE) or not target.is_relative_to(work):
                raise ValueError('Caminho fora do diretório autorizado no mapa de reprodução.')
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        extracted=work/'fontes/anexos/anexos';extracted.mkdir(parents=True)
        with zipfile.ZipFile(work/'fontes/anexos-case-ia.zip') as archive:
            for name in mapping['extrair_do_zip']:
                if PurePosixPath(name).name!=name:raise ValueError('Nome de anexo inválido.')
                (extracted/name).write_bytes(archive.read('anexos/'+name))
        for name in ['preparar.py','referencia.py','pipeline.py','relatorio.py']:
            executar(name,[str(work/name)],work,logs)
        executar('Testes das regras',['-m','unittest','discover','-s','.','-p','test_pipeline.py','-v'],work,logs)
        experiment=work/'experimentos/avaliacao-cega-30'
        for name in ['auditar_amostra.py','verificar_revisao.py','consolidar_adjudicacao.py']:
            executar(name,[str(experiment/name)],work,logs)
        original=(work/'previsao.txt').read_bytes()
        if hashlib.sha256(original).hexdigest()!=manifest['previsao_original_sha256']:
            raise RuntimeError('A previsão numérica/original mudou antes da revisão editorial.')
        revised=explicar_previsao(original.decode('utf-8'))
        assert revised.splitlines()[:4]==original.decode('utf-8').splitlines()[:4]
        (work/'previsao_original.txt').write_bytes(original)
        (work/'previsao.txt').write_bytes(revised.replace('\n','\r\n').encode('utf-8'))
        expected=manifest['entrega_sha256'];actual={name:sha(work/name) for name in expected}
        if expected!=actual:raise RuntimeError('Os arquivos reconstruídos divergem da entrega congelada.')
        with (work/'publicacao.csv').open(encoding='utf-8-sig',newline='') as file:rows=list(csv.DictReader(file))
        counts=dict(collections.Counter(r['decisao'] for r in rows))
        assert len(rows)==359 and len({r['id'] for r in rows})==359
        assert counts=={'publicar':316,'fora':4,'revisar':39}
        adjud=json.loads(next(experiment.glob('adjudicacao_*/metricas_adjudicacao.json')).read_text(encoding='utf-8'))
        assert adjud['cega']['publicadas']['acertos_ramo']==14
        assert adjud['adjudicada']['publicadas']['acertos_ramo']==25
        dest.mkdir(parents=True,exist_ok=True)
        for name in ['publicacao.csv','previsao.txt','previsao_original.txt','arvore.html']:shutil.copy2(work/name,dest/name)
        for source,target in [(work/'dados',dest/'dados_tratados'),(work/'resultados',dest/'metricas'),
                              (work/'leitura',dest/'lotes_leitura'),(work/'referencia',dest/'referencias'),
                              (experiment,dest/'avaliacoes')]:
            shutil.copytree(source,target,dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.py','__pycache__'))
        result={'hashes_identicos':True,'entrega_sha256':actual,'questoes':len(rows),'decisoes':counts,
            'cobertura':316/359,'cega_publicadas':{'acertos':14,'n':26},
            'adjudicada_publicadas':{'acertos':25,'n':26},'testes_pipeline_aprovados':13,
            'testes_organizacao_aprovados':3,
            'segundos_sem_inferencia_gpt':round(time.perf_counter()-start,4),
            'nova_inferencia_executada':False,'api_inferencia_chamada':False,
            'entradas_congeladas_verificadas':len(manifest['entradas_sha256'])}
        result.update({'previsao_numeros_originais_preservados':True,
                       'previsao_original_sha256':hashlib.sha256(original).hexdigest(),
                       'explicacao_previsao_revisada':True})
        (dest/'validacao_final.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (dest/'execucao.log').write_text('\n'.join(logs),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2));print('Saídas reconstruídas: '+str(dest))

if __name__=='__main__':main()
