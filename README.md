# Case Vício — pipeline executado e reproduzível

[![Reproduzir o experimento](https://github.com/romariobc/desafio-vicio-ia/actions/workflows/reproducao.yml/badge.svg)](https://github.com/romariobc/desafio-vicio-ia/actions/workflows/reproducao.yml)

**Versão publicada para conferência do autor. O e-mail de entrega ainda não foi enviado.**

Este repositório registra o que executei para classificar as **359 questões** do desafio. Ele contém as fontes, o tratamento, a árvore de temas, os prompts, as decisões do GPT, a referência humana, a calibração, as regras de publicação e os dois experimentos de revisão.

**Para começar:** baixe ou clone o repositório, entre na pasta e execute `python reproduzir.py`. Não é necessário fornecer uma chave de API, instalar bibliotecas ou acessar outro projeto local. A reprodução funciona sem conexão depois do download.

> **Limite da reprodução:** o comando reconstrói o processamento e as avaliações a partir das decisões de inferência registradas. Ele não chama novamente o GPT. A interpretação das questões ocorreu na conversa do Codex Desktop; os registros dessa interpretação estão em arquivos PSV. O serviço de inferência para novos lotes é uma evolução proposta, não uma automação já executada.

## Consulte pelo celular

- [Relatório para leitura no GitHub](RELATORIO.md) — cópia textual da versão editável.
- [Relatório em Word](RELATORIO.docx) — cinco páginas; ainda sujeito à revisão do autor antes da conversão final para PDF.
- [publicacao.csv](publicacao.csv) — as 359 decisões no contrato solicitado.
- [previsao.txt](previsao.txt) — previsão original e seus intervalos, preservados.
- [Consolidação da adjudicação](execucao/experimentos/avaliacao-cega-30/adjudicacao_83086937fc69/CONSOLIDACAO.md) — resultado e limitações.

## Requisitos

- Python **3.10 ou superior**, com biblioteca padrão. Python 3.12 é a versão usada na integração contínua.
- Windows, Linux ou macOS. No Windows, `py -3` pode substituir `python`; em Linux/macOS, pode ser necessário usar `python3`.
- Git é opcional: serve apenas para clonar. Também é possível usar **Code → Download ZIP** no GitHub e extrair o arquivo.
- Um navegador é necessário somente para abrir os microsites locais.

Não há `pip install` obrigatório, arquivo `.env`, SDK de LLM, banco de dados ou serviço de nuvem necessário para repetir o experimento. Não use `python -O`: as validações internas usam assertions e o comando principal recusa essa opção.

## Reprodução em um comando

Com Git:

```powershell
git clone https://github.com/romariobc/desafio-vicio-ia.git
cd desafio-vicio-ia
python --version
python reproduzir.py
```

Se baixou o ZIP, abra o terminal dentro da pasta extraída e execute apenas os dois últimos comandos. Se `python` não existir no Windows:

```powershell
py -3 --version
py -3 reproduzir.py
```

O programa verifica os hashes das entradas, cria uma área temporária limpa e executa os passos abaixo. **Dados tratados, lotes de leitura, CSVs e métricas não são copiados para essa área: são reconstruídos.** Fontes, decisões de inferência, revisões e contratos congelados são entradas necessárias.

| Passo | Script executado | O que gera ou verifica |
|---|---|---|
| 1 | `execucao/preparar.py` | Fontes e extração do ZIP, limpeza, 359 IDs, 375 temas ativos, parentesco, árvore e 12 lotes de leitura |
| 2 | `execucao/referencia.py` | Normalização dos 60 pareceres antigos e partições fixas de 42/18 |
| 3 | `execucao/pipeline.py` | Decisões R1/R3, comparações R2, calibrador, corte, métricas, `publicacao.csv` e `previsao.txt` |
| 4 | `execucao/relatorio.py` | Árvore navegável e relatório histórico da etapa anterior aos experimentos de 30 questões |
| 5 | `execucao/test_pipeline.py` | 13 testes de integridade e regras, incluindo ancestralidade, extras, abstenção e proteção da calibração |
| 6 | `auditar_amostra.py` | Sorteio reproduzido, composição da amostra, sobreposições e limites amostrais |
| 7 | `verificar_revisao.py` | Integridade da exportação cega, comparação de 30 questões e métricas das 26 publicadas |
| 8 | `consolidar_adjudicacao.py` | Conferência dos 15 desacordos, referência adjudicada e comparação antes/depois |
| 9 | `reproduzir.py` | Comparação dos hashes finais e relatório da reprodução |

Os scripts dos passos 6–8 ficam em `execucao/experimentos/avaliacao-cega-30/`. Os passos são aplicados à cópia temporária; os arquivos entregues na raiz e as evidências versionadas permanecem preservados.

## Onde encontrar as saídas

Depois de uma execução bem-sucedida:

```text
reproducao/
  publicacao.csv             CSV reconstruído
  previsao.txt               previsão reconstruída
  validacao_final.json       contagens, hashes, testes e tempo local
  execucao.log               saída completa dos passos executados
  execucao/
    dados/                   dados tratados e árvore
    leitura/                 lotes usados na leitura
    resultados/              rodadas, calibrador, política e métricas
    experimentos/            auditoria, avaliação cega e adjudicação recalculadas
    arvore.html              árvore navegável reconstruída
```

Para salvar em outra pasta:

```powershell
python reproduzir.py --saida ../minha-reproducao
```

O esperado é: `hashes_identicos: true`, 359 questões, 316 `publicar`, 39 `revisar`, quatro `fora`, 13 testes aprovados, 14/26 na comparação cega e 25/26 na adjudicada. O tempo mostrado mede somente a execução local; exclui a leitura e a classificação pelo GPT e o trabalho do avaliador.

Os hashes dos dois arquivos entregues devem ser exatamente:

```text
publicacao.csv  8fa02999992a217da3173f0af82f0616128e6a1d843ad86cdea476ca4a986ffc
previsao.txt    5033d4bf175080910ab659139aadc570a75880556a962c9bb80713f2e315f5c7
```

## Entenda os arquivos de entrada

```text
publicacao.csv / previsao.txt       saídas congeladas para comparação
manifesto_reproducao.json           hashes das entradas da reprodução atual
configuracao_execucao.json          configuração declarada e ajuste de portabilidade
execucao/
  fontes/                          originais públicos, commit e hashes
  decisoes/r1.psv                   359 decisões semânticas registradas
  decisoes/ajustes_r3.psv            15 ajustes documentados
  prompts.md                       instruções e contrato da inferência
  PLANO_CONGELADO.md                planejamento e limites registrados
  referencia/revisao_humana_original.json
                                   revisão anterior preservada
  resultados/congelamento_r1.json   assinatura da primeira rodada
  resultados/politica_congelada.json
                                   corte, regra de escolha e entradas congeladas
  microsite_avaliacao_cega_30.html   instrumento de revisão sem sugestões
  microsite_adjudicacao_v2.html      instrumento de conferência dos desacordos
  avaliacao_cega_30_*.json/.csv      exportação cega recebida
  adjudicacao_v2_*.json/.csv         adjudicação recebida
  experimentos/avaliacao-cega-30/    scripts, referências e comparações versionadas
```

As fontes vieram de [viciod/case-vicio-ia](https://github.com/viciod/case-vicio-ia/tree/cc8e7eb7bd1069a57634a3e1136b3540c70abb77), commit fixado. O ZIP original e sua extração estão incluídos. Não é necessário rebaixar os anexos ou buscar a antiga pasta `PIPILINE` para reproduzir.

Os relatórios e README dentro de `execucao/` são registros históricos. O README principal é este; o relatório revisado fica na raiz. O gerador histórico não substitui o documento editável.

## O fluxo que realmente executei

1. Tratei HTML, entidades, Unicode e espaços; preservei os originais. Validei IDs e árvore; não fundi nomes de temas repetidos. As disciplinas e assuntos de origem não entraram como rótulos nos lotes de leitura.
2. Na R1, o GPT leu integralmente as 359 questões em 12 lotes e registrou tema, extras, conceito, evidência literal, score bruto e alertas. O contexto da conversa já continha informações anteriores; não alego inferência completamente cega.
3. Na R2, importei a referência humana autorizada: 60 pareceres, com 57 rótulos reconstruíveis e três rejeições sem alternativa. Um “concordo” se refere à sugestão antiga revisada, não valida automaticamente a nova classificação. Separei 42 itens de calibração e 18 de avaliação operacional.
4. Na R3, registrei 15 ajustes, dos quais 13 mudaram o tema central; mantive os demais registros. Calibrei as faixas de score com Beta(1,1), monotonicidade PAVA e escolhi o corte usando somente a calibração. R2 não foi chamada de inferência; R3 não foi uma classificação independente de todo o lote.
5. Congelei a política, gerei a previsão e avaliei a partição operacional. Posteriormente sorteei 30 questões para revisão sem sugestões visíveis, comparei a exportação refeita e construí o segundo microsite para as divergências.
6. O avaliador concluiu a adjudicação. Preservei tanto os rótulos cegos quanto os adjudicados, sem ajustar o modelo ou a previsão ao resultado posterior.

A configuração foi informada pelo autor como **GPT-6.1 Sol, esforço de raciocínio medium, no Codex Desktop**. Os scripts não capturaram o identificador técnico do backend. O manifesto histórico registra essa ausência; `configuracao_execucao.json` acrescenta a identificação declarada posteriormente, sem reescrever o histórico. Não houve API Gemini ou outra chamada de inferência pelos scripts. Não há registros de tokens, custo marginal ou duração integral da inferência. O custo observado foi o uso da assinatura; não atribuo a isso custo total zero.

## Como as regras viram publicar, revisar ou fora

- `publicar`: tema ativo, score bruto ≥ 0,80 e ausência dos alertas bloqueadores definidos em `pipeline.py`.
- `revisar`: abstenção de publicação automática, com sugestão de tema e motivo.
- `fora`: nenhum tema adequado da árvore; não é sinônimo de dúvida comum.
- `confianca`: probabilidade exploratória recalibrada por faixa; não é o score bruto sobre o qual incide o corte.
- Acerto: mesmo tema ou relação ancestral/descendente. Temas irmãos são erro. Um extra correto não corrige tema central errado.

O CSV usa exatamente `id,decisao,tema_central_id,extras_ids,confianca,motivo`, uma linha por questão; extras são separados por `;`. O centro é obrigatório em publicar/revisar e vazio em fora. A confiança pertence a [0,1].

## Interprete a reprodução sem confundir as referências

| Medida | Resultado | Limite |
|---|---:|---|
| Cobertura do lote | 316/359 = 88,02% | Fração publicada; não é tamanho da amostra |
| Previsão original de precisão | 95,37% | Intervalo 90,36%–100% calculado na calibração, otimista após escolha de corte |
| Reservada operacional | 16/16 por ramo | Não cega; referência dirigida |
| Revisão cega nas publicadas | 14/26 = 53,85% | Wilson 35,46%–71,24%; resultado desfavorável preservado |
| Adjudicada nas publicadas | 25/26 = 96,15% | Wilson 81,11%–99,32%; sugestões visíveis na conferência |

Na adjudicação mudaram 14/30 rótulos humanos, não as previsões do modelo. O resultado não mede causalmente redução de ancoragem nem comprova a precisão mínima oficial de 95%. O sorteio foi probabilístico, mas pequeno; três itens já estavam na calibração e a exposição anterior do avaliador não foi confirmada. O relatório apresenta os cálculos e o erro remanescente Q0205. A ausência do gabarito da empresa não impede entregar; a avaliação oficial continua desconhecida.

## Usar os microsites para revisão humana

Depois de baixar o repositório, abra os arquivos HTML de `execucao/` no navegador. Eles funcionam localmente e não enviam respostas a um servidor. O primeiro mostra uma questão por vez sem sugestões; o segundo concentra as 15 divergências e mostra caminhos alternativos sem resposta pré-marcada. Progresso e salvamento local ajudam a retomar, mas **a exportação JSON/CSV é necessária** para transferir as respostas ao pipeline.

Os arquivos publicados são evidências de um experimento encerrado. Para outra revisão, trabalhe em uma cópia/versão nova, registre revisor e exposição prévia, exporte JSON e CSV e confira conclusão, IDs e temas ativos. A primeira exportação deste experimento estava incompleta e foi refeita; não trate clique em “classificada” sem tema escolhido como resposta válida. Não substitua as exportações congeladas nem use a mesma amostra indefinidamente para ajustar e depois alegar teste independente.

## Escala, automação, revisão e manutenção — evolução proposta

Esta seção descreve o que construiria para novos lotes e **50 mil questões por semana**. O código atual é o experimento de 359 questões e contém validações desse universo. Trocar arquivos de entrada não o transforma em serviço genérico.

### Automatizar sem perder o controle

1. Receber importações com versão, validar contrato e preservar fonte bruta. Usar ID/hash para processar apenas itens novos ou alterados; separar inválidos em quarentena.
2. Criar um adaptador de inferência por API com saída estruturada, modelo/versão, prompt, parâmetros, evidências, tokens, custo e latência registrados. Usar fila, concorrência limitada, retentativas com espera e checkpoints. Começar com cinco itens, verificar contrato e custo e só então ampliar.
3. Validar temas ativos e aplicar regras de publicação. Separar referência de desenvolvimento, calibração e teste; validar o calibrador na nova população. Não reutilizar a confiança atual como garantia.
4. Auditar publicadas aleatoriamente, além de revisar casos difíceis e exclusões. Planejar a amostra antes dos resultados; avaliar por disciplina/origem e usar pesos quando a amostragem não for proporcional.
5. Incorporar reportes dos alunos como incidentes: julgamento humano, correção rastreável, análise de causas e teste de regressão. Reduzir automação quando a qualidade não atingir o limite aprovado.

### Ferramentas e critérios para adotá-las

| Necessidade | Começo simples | Quando acrescentar ferramentas |
|---|---|---|
| Dados e histórico | Python, arquivos versionados e armazenamento de objetos; PostgreSQL para estado de produção | Databricks/Delta e ingestão incremental se a empresa já os utiliza ou precisa governar múltiplas fontes; bronze/silver/gold separam bruto, tratado e validado |
| Agendamento e falhas | Job agendado e fila com checkpoints | Prefect ou Airflow quando dependências, retomadas e observabilidade justificarem a operação extra |
| Busca de candidatos | Árvore completa no primeiro teste | Embeddings e pgvector após medir recuperação do tema correto; similaridade não é precisão, sobretudo em temas de fronteira |
| Classificação | LLM com resposta estruturada e regras determinísticas | Classificador treinado quando existir referência suficiente e consistente, comparado à LLM em teste separado |
| Orquestração | Código explícito por etapa | Agentes se houver tarefas variáveis que os justifiquem; não usá-los como “votação” que substitui referência independente |
| Revisão e manutenção | Microsites, auditoria amostral e tabela de erros | Aplicação com autenticação, banco e atribuição de casos quando houver vários revisores, concorrência e necessidade de gestão |
| Verificação do código | Testes e GitHub Actions | Métricas operacionais e alertas em produção: precisão, cobertura, Brier, erro por origem, custo, latência e backlog |

Databricks, embeddings, classificador treinado, APIs e agentes de produção **não foram executados neste case**. Ferramentas adicionais precisam resolver um gargalo mensurável. A projeção de 39/359 para 50 mil implica cerca de 5.432 revisões semanais; com dois minutos por item, aproximadamente 181 horas. É uma hipótese de capacidade, não produtividade medida. Os cenários de custo por API estão no relatório e não são o custo observado do GPT no aplicativo.

### Manter e reavaliar

Versionar taxonomia, prompts, modelo, políticas e referências. Alterar tema ou texto invalida o checkpoint correspondente. Criar nova versão de experimento ao mudar as decisões; nunca apagar o teste que revelou um problema. Conservar a previsão anterior ao resultado que será usado para avaliá-la. Reservar auditorias semanais sem sugestões, rever desacordos com justificativas e manter uma referência de teste fora da escolha do corte.

## Problemas comuns

- **Python não encontrado:** use `py -3` no Windows ou instale Python 3.10+; no Linux/macOS, tente `python3`.
- **Hash de entrada mudou:** baixe uma cópia limpa. Não edite fontes, checkpoints ou revisões para fazer a validação passar. Para outro experimento, crie uma versão separada com novo manifesto e nova avaliação.
- **Mudança após salvar no Excel:** preserve os CSVs originais; Excel pode alterar separador, codificação ou finais de linha. Use uma cópia para análise.
- **Falha de script ou exportação:** o comando encerra com erro; consulte a mensagem e não interprete saídas parciais como uma execução aprovada.
- **Microsite sem respostas antigas:** o armazenamento local depende do navegador e do arquivo/origem. Use as exportações JSON/CSV como registros transferíveis.

## Rastreabilidade da publicação

O pacote preserva `publicacao.csv` e `previsao.txt` sem mudanças. A única adaptação no cálculo histórico para portabilidade foi gravar explicitamente a previsão em CRLF; os bytes finais continuam idênticos. `manifesto_reproducao.json` assina as entradas do pacote atual; `execucao/manifesto_execucao.json` é histórico e não deve ser confundido com o manifesto da publicação. A integração contínua reconstrói o experimento em Windows e Linux. O envio por e-mail aguarda a revisão final do autor.
