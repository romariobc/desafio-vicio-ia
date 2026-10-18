# PIPILINE-GPT — execução nova do case Vício

**359 questões reanalisadas pelo GPT da sessão Codex, sem API externa.** Fontes originais obtidas do GitHub, com verificação de conteúdo pelo hash Git. A entrega anterior foi preservada.

## Comece aqui

- [RELATORIO.md](RELATORIO.md): problema, decisões, números, limitações, produção e memo para o professor.
- [publicacao.csv](publicacao.csv): a entrega final, 359 linhas, cabeçalho original.
- [previsao.txt](previsao.txt): previsão anterior ao uso das métricas reservadas; cobertura exata do lote.
- [dados/arvore_temas.md](dados/arvore_temas.md): árvore ativa, mantendo IDs e parentesco.
- [arvore.html](arvore.html): visualização local da árvore com questões classificadas, filtros e pesquisa.
- [PLANO_CONGELADO.md](PLANO_CONGELADO.md): critérios e limitações registrados antes da R1.

## Como reproduzir

No PowerShell, nesta pasta:

```powershell
.\reproduzir.ps1
# Ou informe o Python >=3.10 disponível:
.\reproduzir.ps1 -Python 'C:\caminho\python.exe'
```

Alternativamente, com Python no PATH:

```powershell
python preparar.py
python referencia.py
python pipeline.py
python relatorio.py
python -m unittest discover -s . -p test_pipeline.py -v
```

Não é necessário instalar SDK ou preencher uma chave. As fontes, decisões e cópia da referência necessárias estão nesta pasta. Os programas escrevem somente nela. Não rode Python com `-O`, pois as validações usam assertions.

**Reprodução significa:** limpar os mesmos dados, validar os registros GPT, reconstruir a referência humana, estimar os scores, aplicar as mesmas decisões e gerar os mesmos CSVs/métricas/relatório. **Não significa:** uma nova chamada à LLM produzindo decisões idênticas. O raciocínio semântico ocorreu nesta conversa e seus checkpoints são `decisoes/r1.psv` e `decisoes/ajustes_r3.psv`.

Para uma nova inferência, forneça as questões tratadas e a árvore ativa ao assistente, siga os prompts em `prompts.md`, registre novas decisões em OUTRA versão e repita a avaliação. Não edite os checkpoints congelados para melhorar o resultado reservado.

## Fluxo realizado

1. **Fontes:** repositório `viciod/case-vicio-ia`, commit `cc8e7eb7bd1069a57634a3e1136b3540c70abb77`; PDF, README e ZIP preservados em `fontes/`. A pasta extraída conserva o caminho interno `anexos/` do ZIP.
2. **Preparação:** HTML para texto, entidades, Unicode NFC e espaços; originais preservados. Questões e árvore validadas em `dados/`. Metadados de origem não entram nos lotes de leitura do classificador.
3. **R1:** leitura integral de 359 questões em 12 lotes; classificação, conceito, trecho literal, alertas e score subjetivo por questão. Publicação preliminar com corte 0,95, anterior à referência, apenas para comparação. Não confundir este corte com precisão de 95%.
4. **R2:** cópia da revisão humana antiga e comparação com os seus rótulos originais reconstruídos. São 60 pareceres: 57 rótulos conhecidos e 3 discordâncias sem alternativa. Partição fixa: 42 para calibração e 18 reservados. A R2 é avaliação/calibração, não uma segunda chamada a modelo.
5. **R3:** reclassificação seletiva a partir dos critérios corrigidos, com 15 registros explícitos de ajustes e lote resultante completo. Os demais registros são mantidos; não houve uma segunda inferência independente de 359 questões. Confiança recalculada por faixas fixas com suavização Beta(1,1) e monotonicidade PAVA. Corte escolhido exclusivamente na calibração.
6. **Avaliação:** política congelada antes de calcular as métricas reservadas. Sem retunar após o resultado. Precisão por ancestralidade, acerto exato, Brier, cobertura e abstenção registrados separadamente.

## Como interpretar os números

- `score_bruto` em `decisoes/` é julgamento subjetivo do GPT, mantido para auditoria.
- `confianca` final é estimativa exploratória da probabilidade de acerto por ramo, aprendida nas faixas de score da referência de calibração. Não há dados suficientes para calibrar cada tema/questão individualmente.
- `publicar` requer tema ativo, ausência de alertas bloqueadores e score bruto acima do corte congelado. O corte incide no score bruto; o CSV expõe a confiança recalibrada. Não confundir as duas escalas.
- `revisar` é abstenção com sugestão; `fora` é exclusão por lacuna. Abstenção total = revisar + fora.
- Um extra correto não corrige um tema central errado. Irmãos não contam como acerto.
- Discordância sem tema alternativo não vira rótulo novo. Se a nova predição repete a antiga rejeitada, há erro conhecido; se muda para outra sugestão sem validação, o resultado permanece desconhecido.

O risco de ancoragem foi aceito pelo usuário pelo prazo e pela experiência do revisor. A amostra original é dirigida; a conversa já teve exposição a resultados anteriores. O reservado é uma separação operacional, **não um teste cego ou amostra representativa**. Os intervalos são descritivos; não comprovam precisão mínima no gabarito oficial da empresa. Não buscamos repetidamente um teste que passe.

## Arquivos auditáveis

```text
fontes/                     originais, texto do PDF e hashes Git/SHA-256
dados/                      questões tratadas, árvore e diagnóstico
leitura/                    12 lotes sem metadados de origem
decisoes/r1.psv              359 análises semânticas novas do assistente
decisoes/ajustes_r3.psv       15 ajustes e motivos
referencia/                 cópia original, normalização, partições e riscos
resultados/r1/              CSV e decisões completas da R1
resultados/r2/              comparação, calibrador e métricas de calibração
resultados/r3/              CSV e decisões completas da R3
resultados/politica_congelada.json
resultados/metricas.json
resultados/comparacao_referencia_r3.csv
resultados/arvore_classificada.json
manifesto_execucao.json      hashes, autoria e limites de reprodução/custo
```

`pipeline.py` recusa alterações de decisões/entradas incompatíveis com o congelamento. `referencia.py` usa a cópia local já recebida: não depende da entrega antiga para reproduzir. Testes verificam integridade, acerto hierárquico, referência parcial, proteção do reservado, calibração e contrato de entrega.

## Tempo, custo e modelo

Inferência: assistente GPT da conversa Codex; identificador comercial exato não confirmado. Nenhuma API externa foi chamada pelos scripts. Tokens e custo marginal por questão não estão disponíveis; não foram inventados. O comando PowerShell mede e informa o tempo de reprodução local, que exclui a leitura/classificação do assistente. As fontes oficiais do desafio permitem usar a própria assinatura, sem exigência de Gemini.
