"""Prepara exclusivamente fontes originais verificadas; não classifica questões."""
import csv
import hashlib
import json
import re
import unicodedata
import zipfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

BASE = Path(__file__).resolve().parent
FONTES = BASE / 'fontes/anexos/anexos'
DADOS = BASE / 'dados'

def salvar_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def csv_ler(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def csv_gravar(path, rows, campos):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(rows)

class Texto(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.hidden = [], 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'): self.hidden += 1
        if tag in ('p', 'br', 'div', 'li', 'tr'): self.parts.append(' ')
    def handle_endtag(self, tag):
        if tag in ('script', 'style'): self.hidden = max(0, self.hidden-1)
        self.parts.append(' ')
    def handle_data(self, data):
        if not self.hidden: self.parts.append(data)

def limpar(s):
    p = Texto(); p.feed(s or '')
    return unicodedata.normalize('NFC', re.sub(r'\s+', ' ', ''.join(p.parts)).strip())

def carregar():
    qs = [json.loads(l) for l in (DADOS/'questoes.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    ts = {t['tema_id']: t for t in csv_ler(DADOS/'temas_ativos.csv')}
    return qs, ts

def main():
    DADOS.mkdir(parents=True, exist_ok=True)
    provenance=json.loads((BASE/'fontes/proveniencia.json').read_text(encoding='utf-8'))
    for record in provenance['arquivos']:
        assert sha(BASE/'fontes'/record['arquivo'])==record['sha256'], ('Fonte original modificada',record['arquivo'])
    with zipfile.ZipFile(BASE/'fontes/anexos-case-ia.zip') as archive:
        for path in FONTES.iterdir():
            if path.is_file():assert path.read_bytes()==archive.read('anexos/'+path.name), ('Extração divergiu do ZIP',path.name)
    raw = [json.loads(l) for l in (FONTES/'questoes.jsonl').read_text(encoding='utf-8-sig').splitlines() if l.strip()]
    temas = csv_ler(FONTES/'temas.csv')
    todos = {t['tema_id']:t for t in temas}
    assert len(todos)==len(temas), 'IDs de tema duplicados'
    ativos = {k:t for k,t in todos.items() if t['status']=='active'}
    assert len(raw)==359 and len({q['id'] for q in raw})==359
    for tid,t in ativos.items():
        seen = {tid}; pai=t['parent_id']
        while pai:
            assert pai in ativos and pai not in seen, ('pai inválido/ciclo',tid)
            seen.add(pai); pai=ativos[pai]['parent_id']
        if t['parent_id']:
            assert int(t['nivel'])==int(ativos[t['parent_id']]['nivel'])+1
        else: assert int(t['nivel'])==0
        path = []; atual=tid
        while atual:
            path.insert(0,ativos[atual]['titulo']); atual=ativos[atual]['parent_id']
        # O caminho original é preservado e uma versão estrutural é derivada.
        t['caminho_derivado']=' > '.join(path)
    tratadas=[]
    for q in raw:
        texto={k:limpar(q.get(k,'')) for k in ('comando',)}
        texto['enunciado']=limpar(q.get('enunciado_html',''))
        texto['alternativas']={k:limpar(v) for k,v in q['alternativas'].items()}
        tratadas.append({**q,**texto})
    (DADOS/'questoes.jsonl').write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n' for q in tratadas),encoding='utf-8')
    csv_gravar(DADOS/'temas_ativos.csv',ativos.values(),list(next(iter(ativos.values()))))
    def node(t):
        return {**t,'filhos':[node(f) for f in ativos.values() if f['parent_id']==t['tema_id']]}
    arvore=[node(t) for t in ativos.values() if not t['parent_id']]
    salvar_json(DADOS/'arvore_temas.json',arvore)
    linhas=['# Taxonomia original ativa','', 'Nenhuma fusão automática de IDs ou definição jurídica adicionada.','']
    def listar(t):
        linhas.append('  '*int(t['nivel'])+f"- {t['tema_id']} | {t['titulo']}" )
        for f in ativos.values():
            if f['parent_id']==t['tema_id']: listar(f)
    for t in ativos.values():
        if not t['parent_id']: listar(t)
    (DADOS/'arvore_temas.md').write_text('\n'.join(linhas)+'\n',encoding='utf-8')
    lotes=BASE/'leitura'; lotes.mkdir(exist_ok=True)
    for start in range(0,len(tratadas),30):
        linhas=[]
        for q in tratadas[start:start+30]:
            linhas += [f"\n{q['id']} | {q['enunciado']} | COMANDO: {q['comando']}"]
            linhas += [f'{k}: {v}' for k,v in q['alternativas'].items()]
        (lotes/f'lote_{start+1:03}_{min(start+30,len(tratadas)):03}.txt').write_text('\n'.join(linhas),encoding='utf-8')
    diag={'questoes':len(raw),'temas':len(temas),'ativos':len(ativos),'inativos':[t['tema_id'] for t in temas if t['status']!='active'],
          'questoes_por_origem':dict(Counter(q.get('disciplina_origem','') for q in raw)),
          'titulos_repetidos':{k:n for k,n in Counter(t['titulo'] for t in ativos.values()).items() if n>1},
          'descricoes_vazias':sum(not t.get('descricao','').strip() for t in ativos.values()),
          'fontes_sha256':{p.name:sha(p) for p in sorted(FONTES.iterdir()) if p.is_file()},
          'transformacoes':['HTML para texto com entidades','NFC','espaços normalizados','HTML e metadados originais preservados','metadados não usados como rótulos'],
          'modelo':'nenhum; preparação determinística','arvore_valida':True}
    salvar_json(DADOS/'diagnostico.json',diag)
    print(json.dumps(diag,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
