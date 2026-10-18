"""Relatório e árvore local gerados das métricas reais; não contém números fixos de desempenho."""
import json
from pathlib import Path
from preparar import BASE, carregar, csv_ler, salvar_json, sha

def pct(x):return 'indefinido' if x is None else f'{100*x:.2f}%'
def rate(s):
    n=s['n_avaliaveis_incluindo_rejeicoes'];return f"{s['acertos_ramo']}/{n} ({pct(s['precisao_incluindo_rejeicoes_conhecidas'])})" if n else 'indefinida'

def main():
    m=json.loads((BASE/'resultados/metricas.json').read_text(encoding='utf-8'))
    frozen=json.loads((BASE/'resultados/politica_congelada.json').read_text(encoding='utf-8'))
    p=frozen['politica'];allm=m['referencia_completa_descritiva'];test=m['avaliacao_reservada'];cal=m['calibracao']
    final=allm['r3'];n=final['total_lote'];c=final['decisoes'];a=test['r3']['publicadas_na_referencia']
    ic=a['wilson_95_condicional'];bc1=test['r1']['referencia_toda']['brier_central'];bc3=test['r3']['referencia_toda']['brier_central']
    forecast=(BASE/'previsao.txt').read_text(encoding='utf-8').splitlines()[0].split(': ')[1]
    report=f'''# Case Vício — classificação hierárquica com GPT e abstenção

Execução de 18/10/2026. Fontes do [repositório oficial](https://github.com/viciod/case-vicio-ia/tree/cc8e7eb7bd1069a57634a3e1136b3540c70abb77), commit fixado e conteúdo verificado por hash. Relatório conciso organizado em cinco partes, incluindo memo.

## 1. Problema, hipóteses e execução

O aluno procura um tópico e recebe questões. O erro de publicação custa aprendizado incorreto; revisão custa tempo do professor. O desafio pede maximizar cobertura respeitando pelo menos 95% de acerto nas publicadas. Acerto é tema exato ou ancestral/descendente, nunca irmão. Os rótulos oficiais existem, mas são reservados pela empresa; não foram acessados.

Hipótese inicial: uma LLM interpreta melhor o conteúdo do que metadados de origem, mas sua confiança subjetiva não basta para decidir publicação. O GPT da sessão leu as 359 questões completas em 12 lotes, usando a árvore ativa, e registrou tema, conceito, evidência literal, score e alertas por questão. Não usamos nem executamos Gemini. Código Python trata os dados, valida e reproduz o pós-processamento; as decisões de inferência estão nos arquivos PSV. Identificador comercial exato e tokens faturados não foram expostos pelo ambiente.

O plano foi registrado antes da nova R1. A R1 foi congelada antes da importação normalizada da referência. A sessão contém histórico anterior: esta é uma reanálise com exposição prévia, não inferência cega. R1: classificação nova. R2: confronto com referência e calibração. R3: reclassificação seletiva documentada, preservando os demais registros e aplicando a política ao lote completo; não é uma nova inferência independente de 359 itens.

Descartamos metadados como rótulos, confiança >=0,98 como suposta prova de precisão, fusão automática de homônimos e promoção ao pai pela mera presença de extras. Também descartamos ajustar repetidamente após olhar a avaliação reservada. Score inicial é subjetivo; calibração estima acerto com dados de referência, distinção discutida por [Guo et al.](https://proceedings.mlr.press/v70/guo17a.html). A possibilidade de abster-se é a base do compromisso risco/cobertura de [El-Yaniv e Wiener](https://www.jmlr.org/papers/v11/el-yaniv10a.html).

## 2. Dados, diagnóstico e referência

São 359 IDs únicos e 377 temas, dos quais 375 ativos e 2 inativos (5078 e 5234). A preparação valida unicidade, parentesco, níveis e ciclos; preserva fontes, HTML e IDs; converte entidades/HTML em texto e normaliza NFC e espaços. A árvore não recebeu definições jurídicas inventadas. Há oito títulos repetidos e 20 descrições vazias. Muitas descrições restantes só repetem a hierarquia e a contagem no sistema de origem: não são definições de inclusão/exclusão.

Problemas relevantes: comandos genéricos; metadados errados; homônimos entre disciplinas; questões com vários subtemas; mosaicos entre ramos e contexto incompleto. Q0219 menciona participação necessária sem fornecer a situação antecedente e fica em revisão. Q0020 reúne temas sem um foco único e não é liberada só porque a raiz Penal contém tudo. Q0298 cobra relações de consumo na Lei 8137, enquanto o nó disponível diz especificamente CDC; não tratamos os dois como equivalentes.

A revisão anterior tem 60 pareceres: 54 concordâncias, 3 concordâncias no pai e 3 discordâncias sem tema corrigido. Reconstruímos os 57 rótulos positivos pelos IDs ANTIGOS mostrados ao revisor. Q0028, Q0053 e Q0168 fornecem restrições negativas, não um gabarito alternativo. Quando a nova sugestão repete o ID rejeitado, o erro conhecido entra no denominador específico; não é descartado para inflar precisão.

**Ancoragem aceita pelo usuário:** prazo curto, otimização do tempo e experiência do revisor. Esse motivo foi registrado, mas não elimina o viés. Identidade/credenciais e duração da revisão não são comprovadas pelo JSON. A seleção original é dirigida, sem probabilidades de inclusão conhecidas. Uma partição determinística gerou 42 pareceres para calibração e 18 reservados; a separação operacional segue o cuidado com vazamento descrito na [documentação do scikit-learn](https://scikit-learn.org/stable/common_pitfalls.html), sem alegar que recupera um teste cego após a exposição histórica.

## 3. Ajustes, confiança e resultados

Na calibração, R1 confundiu 4388 (Teorias Criminológicas em Espécie) com o irmão 4387 (Teorias de Nível Sociológico) em Q0024 e Q0031. A R3 corrigiu esses casos e outros de mesmo conceito sociológico, com justificativa por ID. Revisou ainda dolo geral, prisão domiciliar na execução e fraude patrimonial. Existem {m['alteracoes_semanticas']} registros de ajustes, dos quais {m['r3_vs_r1_temas_alterados']} mudam o tema central. Q0053 e Q0168 receberam sugestão conservadora, mas continuam em revisão por referência inconclusiva.

Confiança: faixas fixas do score (<0,80; 0,80–0,9499; >=0,95), com média posterior Beta(1,1), (acertos+1)/(n+2), e agrupamento monotônico PAVA quando necessário. Não se trata de temperature scaling, fine-tuning ou comprovação de probabilidades individuais. Na calibração R3, as faixas média/alta tiveram 10/10 e 26/26 acertos e estimativas suavizadas de 0,9167 e 0,9643; a faixa baixa não tem rótulos centrais e usa apenas o prior 0,5, devendo ser retida. O score bruto é preservado em paralelo.

A política compara cortes predefinidos, exige >=95% de acerto pontual e pelo menos 8 publicadas avaliáveis na calibração, bloqueia mosaicos, raízes genéricas, texto insuficiente e referência inconclusiva, e maximiza a cobertura. O corte escolhido foi {p['corte_escolhido']:.2f} no SCORE BRUTO; a coluna de confiança final usa outra escala, recalibrada. O critério de 8 é operacional, não demonstra poder estatístico. A política foi congelada antes de calcular as métricas reservadas.

| Medida | R1 preliminar | R3 final |
|---|---:|---:|
| Publicar | {allm['r1']['decisoes'].get('publicar',0)} | {c['publicar']} |
| Revisar | {allm['r1']['decisoes'].get('revisar',0)} | {c['revisar']} |
| Fora | {allm['r1']['decisoes'].get('fora',0)} | {c['fora']} |
| Cobertura no lote | {pct(allm['r1']['cobertura'])} | {pct(final['cobertura'])} |
| Abstenção (revisar + fora) | {pct(allm['r1']['abstencao_total'])} | {pct(final['abstencao_total'])} |
| Precisão nas publicadas avaliáveis da calibração, incluindo rejeições conhecidas | {rate(cal['r1']['publicadas_na_referencia'])} | {rate(cal['r3']['publicadas_na_referencia'])} |
| Precisão nas publicadas da avaliação reservada | {rate(test['r1']['publicadas_na_referencia'])} | {rate(a)} |

R3: intervalo Wilson descritivo das publicadas reservadas **{pct(ic[0])}–{pct(ic[1])}**; acerto EXATO nesse subconjunto: {a['acertos_exatos']}/{a['referencias_completas']}. Considerando os 57 rótulos completos, o acerto por ramo é 57/57; nas publicadas com esses rótulos é 52/52. Estes últimos números incluem desenvolvimento e não são teste independente.

Brier no mesmo conjunto reservado de 17 predições com tema central: {bc1:.6f} na R1 e {bc3:.6f} na R3; menor é melhor. Não comparamos Brier de subconjuntos publicados diferentes como se fossem a mesma população. A faixa baixa permanece pouco informativa. A previsão congelada baseada na calibração é {float(forecast)*100:.2f}% de precisão, com cobertura exata de {pct(final['cobertura'])}. Os intervalos da previsão usam a calibração e são otimistas após seleção do corte; não são garantia estatística.

**Conclusão da avaliação:** a meta pontual foi atingida na referência reservada disponível; a precisão mínima de 95% no lote/gabarito oficial **não está comprovada**. Dezesseis acertos não justificam afirmar certeza sobre os outros itens. Não repetimos o ajuste até o teste passar. Como dimensão aproximada, 73 acertos em 73 amostras independentes produzem limite inferior Wilson de cerca de 95%; ainda seriam necessários amostragem adequada e controle dos vieses.

## 4. Produção, custo e operação

Para 50 mil questões semanais: validar importação e HTML; versionar taxonomia; obter candidatos por embeddings quando houver ganho medido contra árvore completa; usar LLM com saída estruturada; validar IDs/evidência; decidir por política congelada; encaminhar incerteza ao especialista. Um classificador supervisionado leve passa a fazer sentido após formar rótulos confiáveis. Agentes podem organizar etapas e curadoria; sua concordância não substitui referência. Nenhum desses componentes de produção foi implantado aqui.

Monitorar precisão por disciplina e por coorte, cobertura/abstenção, tempo de revisão, erros entre irmãos, lacunas e reportes de alunos; sortear auditorias também entre publicadas e fora. Separar dados para ajuste e avaliação, adjudicar divergências e reavaliar após mudanças da taxonomia. Guardar versões de modelo/prompt/entradas, latência, tokens e custos. Usar uma nova amostra independente para validar a política antes de operação real.

Nesta execução não houve API externa: custo incremental monetário e tokens não foram medidos; não são zero comprovado. O comando de reprodução mede somente o processamento local, excluindo inferência do assistente. Para orçar API em produção: custo/questão = tokens_entrada × preço_entrada/1 milhão + tokens_saída × preço_saída/1 milhão. **Simulação hipotética, não cotação nem medição:** preços de US$1/US$5 por milhão e 200 tokens de saída dariam US$0,0025 por questão com 1.500 tokens de entrada (US$125/50 mil), ou US$0,013 com 12.000 (US$650/50 mil), antes de retries, reanálise e revisão humana. Trocar pelas tarifas/tokens reais ao escolher fornecedor. Repetir a taxonomia pode dominar o custo; cache/batch/retrieval exigem teste e instrumentação, não foram usados aqui.

## 5. Memo para o professor

Professor(a), organizamos o lote para que o aluno receba questões relacionadas ao tópico que escolheu. Há **{c['publicar']} propostas de publicação**, **{c['revisar']} para revisão** e **{c['fora']} fora por lacuna ou por matéria externa**. O resultado da pequena referência disponível é favorável, mas não garante o mesmo acerto nas demais questões.

Encontramos títulos repetidos em caminhos diferentes, tópicos sem descrição e perguntas que misturam assuntos. Pedimos critérios de inclusão/exclusão para homônimos, em especial as teorias criminológicas e a legislação especial. Recomendamos examinar as 20 descrições vazias, sem apagar IDs históricos automaticamente. A árvore original foi preservada.

Prioridades de curadoria: confirmar o enquadramento dos crimes esportivos de Q0168; decidir onde acolher o rito dos crimes funcionais de Q0017 e o cartel de Q0039; recuperar o contexto de Q0219; e estabelecer uma regra pedagógica para questões mosaico. Em Q0028 e Q0053 há sugestão no pai, mas a discordância antiga não validou um substituto, por isso permanecem em revisão.

O microsite anterior mostrou a sugestão ao revisor para economizar tempo; essa limitação foi aceita e registrada. Para validar a próxima versão, precisamos de uma auditoria nova de publicadas, com análise inicial sem sugestão, e de identificação do revisor e do critério adotado. Separar esclarecimento da taxonomia de decisão sobre cada questão evita corrigir o tópico errado por uma palavra do cenário.
'''
    (BASE/'RELATORIO.md').write_text(report,encoding='utf-8')
    # Árvore offline: dados serializados com '<' escapado e renderização por textContent.
    qs,temas=carregar();rows=csv_ler(BASE/'publicacao.csv');rm={r['id']:r for r in rows}
    payload={'temas':list(temas.values()),'questoes':[{'id':q['id'],'texto':q['enunciado'],'comando':q['comando'],
        'alternativas':q['alternativas'],'classificacao':rm[q['id']]} for q in qs]}
    data=json.dumps(payload,ensure_ascii=False).replace('<','\\u003c')
    html='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Árvore e decisões — PIPILINE-GPT</title><style>
body{font:15px/1.5 system-ui;margin:0;color:#17243a;background:#f5f7fa}header{background:#102b43;color:white;padding:22px 30px}h1{font-size:24px;margin:0}p{margin:8px 0}main{display:grid;grid-template-columns:370px 1fr;gap:22px;padding:24px}nav,article{background:white;border:1px solid #d7e1e8;border-radius:12px;padding:18px}nav{max-height:80vh;overflow:auto}button,select,input{font:inherit;padding:7px;border:1px solid #cbd5e1;border-radius:6px}button{background:#eff5fa;cursor:pointer;text-align:left;margin:3px}summary{cursor:pointer;padding:4px}.item{border-bottom:1px solid #d8e1e8;padding:16px 0}.badge{display:inline-block;background:#e6eff4;padding:2px 8px;border-radius:15px}.publicar{background:#dcf3e9}.revisar{background:#fff0cb}.fora{background:#f4e0e0}#busca{width:65%}small{color:#51647b}details details{margin-left:15px}@media(max-width:800px){main{display:block}nav{max-height:350px;margin-bottom:20px}}</style>
<header><h1>Árvore de temas e questões</h1><p id="numeros"></p><small style="color:#c8deea">GPT da sessão Codex · referência parcial e ancoragem registrada · precisão oficial não comprovada</small></header>
<main><nav><button id="todas">Todas as questões</button><div id="arvore"></div><button id="fora">Fora da árvore</button></nav><article>
<label>Pesquisar <input id="busca" placeholder="ID, texto, conceito ou caminho"></label> <select id="status"><option value="">Todas as decisões</option><option>publicar</option><option>revisar</option><option>fora</option></select>
<h2 id="titulo">Todas as questões</h2><small id="aviso">Contagens incluem descendentes; extras não mudam o tema central.</small><div id="lista"></div></article></main>
<script id="dados" type="application/json">__DATA__</script><script>
const d=JSON.parse(document.getElementById('dados').textContent), temas=new Map(d.temas.map(t=>[t.tema_id,t]));let no='';
function desc(id,other){while(other){if(id===other)return true;other=temas.get(other)?.parent_id||''}return false}
function e(tag,text,cls){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el}
function quantidade(id){return d.questoes.filter(q=>desc(id,q.classificacao.tema_central_id)).length}
function tree(t){const det=e('details'),sum=e('summary',t.tema_id+' · '+t.titulo+' ('+quantidade(t.tema_id)+')');det.append(sum);const btn=e('button','Ver questões deste ramo');btn.onclick=()=>{no=t.tema_id;render()};det.append(btn);for(const f of d.temas.filter(f=>f.parent_id===t.tema_id))det.append(tree(f));return det}
for(const t of d.temas.filter(t=>!t.parent_id))document.getElementById('arvore').append(tree(t));
const counts={};for(const q of d.questoes)counts[q.classificacao.decisao]=(counts[q.classificacao.decisao]||0)+1;
document.getElementById('numeros').textContent=d.questoes.length+' questões · '+d.temas.length+' temas ativos · '+Object.entries(counts).map(([k,v])=>v+' '+k).join(' · ');
function render(){const search=document.getElementById('busca').value.toLocaleLowerCase('pt-BR'),status=document.getElementById('status').value;
const items=d.questoes.filter(q=>{const c=q.classificacao,t=temas.get(c.tema_central_id);return (!no||(no==='fora'?!c.tema_central_id:desc(no,c.tema_central_id)))&&(!status||c.decisao===status)&&JSON.stringify([q.id,q.texto,q.comando,q.alternativas,t?.caminho,c.motivo]).toLocaleLowerCase('pt-BR').includes(search)});
document.getElementById('titulo').textContent=(no==='fora'?'Fora da árvore':temas.get(no)?.caminho||'Todas as questões')+' · '+items.length;
const lista=document.getElementById('lista');lista.replaceChildren();for(const q of items){const c=q.classificacao,el=e('section',undefined,'item');el.append(e('strong',q.id+' '),e('span',c.decisao,'badge '+c.decisao),e('p',temas.get(c.tema_central_id)?.caminho||'Sem tema aplicável'),e('small','Confiança estimada: '+c.confianca+' · extras: '+(c.extras_ids||'nenhum')),e('p',q.texto));if(q.comando)el.append(e('p','Comando: '+q.comando));const alt=e('details');alt.append(e('summary','Alternativas e motivo'));for(const [k,v] of Object.entries(q.alternativas))alt.append(e('p',k+': '+v));alt.append(e('p','Motivo: '+c.motivo));el.append(alt);lista.append(el)}}
document.getElementById('todas').onclick=()=>{no='';render()};document.getElementById('fora').onclick=()=>{no='fora';render()};document.getElementById('busca').oninput=render;document.getElementById('status').onchange=render;render();
</script></html>'''.replace('__DATA__',data)
    (BASE/'arvore.html').write_text(html,encoding='utf-8')
    # Atualiza a lista de hashes depois dos artefatos do relatório.
    manifest=BASE/'manifesto_execucao.json'
    mm=json.loads(manifest.read_text(encoding='utf-8'))
    mm['arquivos_sha256']={str(p.relative_to(BASE)).replace('\\','/'):sha(p) for p in sorted(BASE.rglob('*'))
        if p.is_file() and '__pycache__' not in p.parts and p.name!='manifesto_execucao.json'}
    salvar_json(manifest,mm)
    print('Relatório e árvore gerados diretamente das métricas; manifesto atualizado.')

if __name__=='__main__':main()
