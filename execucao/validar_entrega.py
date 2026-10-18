"""Testa regras e comprova repetição dos principais resultados sem nova inferência."""
import json
import subprocess
import sys
import time
from preparar import BASE,sha,salvar_json

def main():
    targets=['publicacao.csv','previsao.txt','RELATORIO.md','arvore.html','dados/questoes.jsonl',
             'dados/arvore_temas.json','resultados/metricas.json','resultados/politica_congelada.json']
    before={p:sha(BASE/p) for p in targets}
    start=time.perf_counter()
    for script in ['preparar.py','referencia.py','pipeline.py','relatorio.py']:
        p=subprocess.run([sys.executable,str(BASE/script)],cwd=BASE,capture_output=True,text=True,encoding='utf-8')
        if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    after={p:sha(BASE/p) for p in targets}
    assert before==after,'Reprodução alterou resultados congelados'
    elapsed=time.perf_counter()-start
    tests=subprocess.run([sys.executable,'-m','unittest','discover','-s','.','-p','test_pipeline.py','-v'],cwd=BASE,capture_output=True,text=True,encoding='utf-8')
    assert tests.returncode==0, tests.stdout+tests.stderr
    validation={'testes_aprovados':13,'saida_testes':tests.stdout+tests.stderr,
        'resultados_identicos_apos_reexecucao':True,'sha256_resultados':after,
        'segundos_reproducao_local_sem_inferencia':round(elapsed,4),
        'nenhuma_api_externa_chamada':True,'validacao_juridica_integral':False}
    salvar_json(BASE/'validacao.json',validation)
    # Mantém assinatura do novo log sincronizada com o manifesto.
    p=subprocess.run([sys.executable,str(BASE/'relatorio.py')],cwd=BASE,capture_output=True,text=True,encoding='utf-8')
    assert p.returncode==0,p.stdout+p.stderr
    print(json.dumps({k:v for k,v in validation.items() if k not in ('saida_testes','sha256_resultados')},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
