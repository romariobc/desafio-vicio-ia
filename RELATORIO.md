<!-- Cópia textual do DOCX para consulta no GitHub. Documento editável: RELATORIO.docx. -->

# Classificação de questões jurídicas com avaliação humana

## Resumo

Construí um fluxo de classificação para decidir quais questões poderiam chegar ao aluno, quais exigiriam revisão e quais não encontrariam tema adequado. Analisei as 359 questões do desafio com apoio do GPT no aplicativo Codex Desktop, tratei os dados e registrei as decisões para reprodução. Publiquei como decisão experimental 316 questões, cobertura de 88,02%, e preservei minha previsão de precisão de 95,37%. Na amostra, obtive concordância de 53,85% na revisão cega e 96,15% após a conferência das divergências com sugestões visíveis. Não interpreto esse segundo resultado como comprovação de precisão mínima de 95% no gabarito oficial. Entrego o caminho, os cálculos e os limites que sustentam essa conclusão.

## Introdução

Entendi que o problema central era proteger o percurso de estudo: uma questão no tema errado pode fazer o aluno estudar um conteúdo diferente do procurado. Por isso, parti da hipótese de que a leitura do comando e das alternativas, combinada ao caminho completo da árvore, seria mais útil que aceitar a classificação de origem. Reconheci antes do código que a semântica e a confiança declarada pelo modelo poderiam produzir respostas plausíveis e incorretas. Planejei tratamento, registro de evidências, abstenção e avaliação humana, em vez de transformar toda sugestão em publicação.

Usei como fonte o repositório oficial e seu LEIA-ME [1]. A empresa possui rótulos reservados; eu não tive acesso a eles. Entendi que estimar a própria precisão sem esse gabarito fazia parte do desafio e não impedia a entrega. A revisão humana local é minha referência experimental, sujeita a erros e exposição às sugestões.

## Objetivos gerais

Meu objetivo foi maximizar a fração publicada, buscando pelo menos 95% de acerto nas questões publicadas segundo a régua do desafio, e antecipar com intervalos meu próprio resultado. Também procurei demonstrar meu raciocínio, diagnosticar dificuldades, desenhar uma operação semanal de 50 mil questões e comunicar as decisões de forma compreensível ao professor. Considerei acerto o tema exato ou seu ancestral/descendente; temas irmãos contam como erro.

## Objetivos específicos

Organizei seis passos e seus artefatos: (1) preservar fontes e hashes; (2) limpar HTML e validar IDs, gerando dados tratados e árvore; (3) classificar com conceito, evidência, extras, alertas e score, salvando checkpoints; (4) comparar com referência humana e calibrar a confiança; (5) congelar a política e auditar uma amostra cega, preservando a adjudicação posterior; (6) gerar publicacao.csv, previsao.txt, métricas, prompts, código e este relatório com memo ao professor. Separei a reprodução dessas decisões da automação de novas inferências, ainda não implementada.

## Metodologia aplicada

### Preparação e classificação

Preservei os originais no commit cc8e7eb7bd1069a57634a3e1136b3540c70abb77. Normalizei entidades HTML, Unicode e espaços, mantendo texto e metadados originais para auditoria. Validei 359 questões e 377 temas, dos quais 375 ativos. Excluí candidatos inativos, conferi parentesco e ciclos e retirei disciplina e assunto de origem dos lotes apresentados ao classificador.

Registrei a configuração utilizada como GPT-6.1 Sol, esforço de raciocínio medium, diretamente no Codex Desktop, conforme minha identificação no aplicativo; os scripts não capturaram um identificador técnico do backend. Não executei API Gemini ou outra API de inferência. O GPT auxiliou tanto a classificação quanto os scripts. Registrei a leitura das 359 questões em 12 lotes na R1; a R2 foi comparação/calibração; na R3 fiz 15 ajustes documentados, com 13 mudanças de tema central. Não tratei essas etapas como três modelos ou três inferências completas independentes.

### Calibração e política de decisão

Importei 60 pareceres humanos anteriores: 57 rótulos reconstruíveis e três rejeições sem alternativa. Separei 42 para calibração e 18 para avaliação operacional, com semente fixa. Aceitei a ancoragem da revisão inicial pelo prazo e experiência do revisor, registrando o risco. Para distinguir score e probabilidade calibrada [2], usei faixas fixas de score: abaixo de 0,80; de 0,80 a menos de 0,95; e de 0,95 em diante. Estimei a chance de acerto por ramo com prior Beta(1,1):

q = (k + 1)/(n + 2) ;   q(média) = (10 + 1)/(10 + 2) = 0,9167 ;   q(alta) = (26 + 1)/(26 + 2) = 0,9643

Apliquei monotonicidade PAVA para impedir que uma faixa de score maior recebesse confiança menor. Escolhi, somente na calibração, o corte de maior cobertura entre os predefinidos que atingia precisão pontual ≥ 95% e ao menos oito rótulos avaliáveis. O corte foi 0,80 no score bruto; no CSV, apresento a confiança recalibrada. Bloqueei publicação por alertas de texto, tema genérico, mistura de assuntos ou lacuna da árvore. Não usei a avaliação posterior para retunar o corte.

### Amostragem e intervalos

Sorteei 30 das 359 questões sem reposição; cada questão teve probabilidade de inclusão 30/359 = 8,36%. A semente e a ordem estão registradas. A amostra contém 26 publicadas e quatro revisar; três itens já pertenciam à calibração anterior. Não confirmei ausência de exposição prévia do avaliador. Para k acertos em n itens, calculei p̂ = k/n e o intervalo Wilson bilateral de 95%, com z = 1,96 [3]:

IC = C ± R ;   C = (p̂ + (z^(2))/(2n))/(1 + (z^(2))/(n))

R = (z√((p̂(1 − p̂))/(n) + (z^(2))/(4n^(2))))/(1 + (z^(2))/(n))

Uso esses intervalos como descritivos: eles não corrigem ancoragem, seleção de corte nem erro da referência. Não interpreto 95% de confiança como 95% de chance de cada resposta estar correta.

## Resultados obtidos e cálculos comprobatórios

Obtive 316 publicar, 39 revisar e quatro fora. Calculei cobertura = 316/359 = 88,02%; revisão = 39/359 = 10,86%; fora = 4/359 = 1,11%; abstenção total = 43/359 = 11,98%. A cobertura é conhecida para o lote completo, não corresponde aos 30 itens da auditoria. Preservei no previsao.txt a precisão de 95,37%, média das probabilidades calibradas das publicadas, e seu intervalo original de 90,36%–100%. Esse intervalo veio de 36/36 na calibração após selecionar o corte, portanto reconheço seu otimismo. Para a cobertura deste lote, o intervalo é 88,02%–88,02%.

| Referência | Acertos por ramo | Wilson de 95% |
| --- | --- | --- |
| Reservada operacional não cega | 16/16 = 100% | 80,64%–100% |
| Revisão cega | 14/26 = 53,85% | 35,46%–71,24% |
| Adjudicada com sugestões visíveis | 25/26 = 96,15% | 81,11%–99,32% |

Na adjudicada, o acerto exato foi 22/26 = 84,62%, distinto da regra por ramo permitida. Minha previsão diferiu em +0,78 ponto percentual do resultado adjudicado e superestimou a concordância cega em 41,52 pontos. Não apresento apenas o resultado favorável: os arquivos preservam as duas referências e a divergência remanescente Q0205.

Conferi 15 divergências; o avaliador adotou o tema do modelo em 14. Assim, a referência mudou em 14/30 = 46,67% da amostra e em 14/15 = 93,33% dos desacordos. Não atribuo causalmente essa mudança à redução de ancoragem: a conferência voltou a mostrar as sugestões. Mantive modelo e previsão intactos. Calculei Brier como a média de (q − y)², com y igual a 1 no acerto por ramo e 0 no erro: 0,4133 na cega e 0,0351 na adjudicada. Como só y mudou, a melhora não comprova nova calibração do modelo.

Amostra aleatória não significa amostra suficiente. Penal ocupou 17/30 da amostra, contra 146/359 do lote. Mesmo 26/26 dariam limite Wilson inferior de 87,13%. Nas 316 publicadas, 16 erros já violariam 95%: 300/316 = 94,94%. A chance de sortear 26 sem detectar esses 16 erros seria C(300,26)/C(316,26) = 24,44%, sendo C a combinação sem reposição. Sob política fixa, referência adequada e zero erros, seriam necessários pelo menos 53 itens para essa probabilidade cair a ≤ 5%; não adoto esse número como plano universal para qualquer resultado observado.

### Diagnóstico e problemas encontrados

Identifiquei oito títulos repetidos e vinte descrições vazias. Questões de fronteira e cenários parecidos podem exigir institutos jurídicos diferentes; proximidade semântica não garante enquadramento. Embeddings poderiam atribuir similaridades próximas a temas distintos, mas não os executei neste experimento. Mantenho auditoria humana contínua, sem presumir que toda publicação precise de revisão manual individual. Do lado humano, reconheço a necessidade de expertise no domínio e critérios claros entre temas vizinhos; não inferi falta de competência pela discordância. A exportação inicial incompleta exigiu refazer a revisão. Descartei tratar confiança subjetiva, origem, acordo entre rodadas ou a promoção indiscriminada ao pai como provas de acerto.

## Defesa do workflow para aumento de escala

### Importação e escolha das técnicas

Para 50 mil questões semanais, eu preservaria o mesmo encadeamento de responsabilidades: importação versionada, validação, normalização, classificação, decisão, revisão e publicação auditável. Processaria apenas itens novos ou alterados, usando ID e hash, com fila, concorrência limitada, controle de limites da API, tentativas com espera e checkpoints. Associaria cada decisão à versão do texto, da árvore, do prompt, do modelo e do calibrador, permitindo rastrear e desfazer uma publicação.

Eu usaria embeddings para recuperar candidatos, medindo antes se o tema correto aparece entre eles. Similaridade próxima entre temas de fronteira exigiria mais contexto e eventual abstenção; não usaria o maior valor de similaridade como probabilidade de acerto. Uma LLM interpretaria comando e alternativas e retornaria IDs ativos, evidência e alertas em formato validado. Após reunir referências consistentes, compararia um classificador treinado, potencialmente mais barato, com a LLM em teste separado. Eu reservaria agentes para orquestração de tarefas, falhas e registros; sua concordância não substituiria revisão independente. Essa classificação com rejeição busca equilibrar risco e cobertura [4].

Eu começaria com armazenamento versionado, banco relacional e processamento em lote. Se já houvesse Databricks na empresa ou necessidade de governar várias importações, usaria camadas bronze para dados brutos, silver para dados tratados e gold para decisões validadas; ingestão incremental e quarentena preservariam erros para diagnóstico [5]. Não considero Databricks obrigatório pelo volume isolado, nem o utilizei aqui.

### Custo médio estimado por questão

Meu custo observado foi o uso da assinatura do aplicativo; não medi tokens, duração integral da inferência ou custo marginal por questão. Para orçar uma futura API, adoto como cenário um modelo diferente, GPT-5.4 Mini, que precisaria passar por avaliação antes de substituir o GPT utilizado. Na tabela consultada em 18/10/2026, entrada custa US$ 0,75 e saída US$ 4,50 por milhão de tokens [6]. Com 1.500 tokens de entrada e 200 de saída, calculo (1.500 × 0,75 + 200 × 4,50)/1.000.000 = US$ 0,002025 por questão; para 50 mil, US$ 101,25. Com 12 mil tokens de entrada, seriam US$ 0,0099 por questão e US$ 495 por semana. Não são médias observadas nem preços do GPT-6.1 Sol; são cenários sem cache, reprocessamento, embeddings, infraestrutura, tributos ou trabalho humano.

Mantida apenas como hipótese a proporção de revisão de 39/359, eu receberia cerca de 5.432 questões por semana. A dois minutos por item, precisaria de aproximadamente 181 horas de revisão. Esse cálculo mostra que reduzir custo de tokens não resolve sozinho o gargalo: eu priorizaria casos de risco, melhoraria os temas e mediria o tempo real antes de dimensionar a equipe.

### Qualidade contínua e participação humana

Eu reservaria amostras semanais aleatórias das publicadas para avaliação sem sugestões, além de revisar casos difíceis e exclusões. Fixaria tamanho e critérios antes de ver resultados; estratificaria por disciplina e importação quando necessário, usando pesos para estimativas globais. Acompanharia precisão por ramo e exata, cobertura, intervalos, Brier, custo, latência e erros por origem. Quando o risco excedesse o limite aprovado, reduziria a publicação automática e só recalibraria com separação entre desenvolvimento e teste. Reportes de alunos entrariam como incidentes com julgamento humano, correção rastreável e teste de regressão. Eu manteria os minisites com uma questão por vez, progresso, busca e exportação validada; no de divergências, mostraria os caminhos sem escolha pré-marcada. Defendo esse desenho pela auditabilidade e pelo uso seletivo do professor; ainda não medi sua produtividade ou satisfação.

## Memo para o professor

Professor, organizei este experimento para que o aluno encontre questões do conhecimento que precisa estudar. Encontrei situações em que o texto menciona um crime, mas exige conhecimento de outro assunto, como um recurso processual. Por isso, procurei classificar pelo conhecimento necessário para responder, e não apenas pelas palavras mais parecidas.

Recomendo manter os identificadores dos temas e sempre mostrar o caminho completo. Peço sua ajuda para escrever definições curtas, exemplos do que entra e do que não entra em cada assunto, especialmente nos temas vizinhos. Antes de criar categorias, eu revisaria as lacunas apontadas pelas questões fora. Evitaria usar temas introdutórios como destino de toda dúvida.

Preciso de seu julgamento nas questões com vários conhecimentos e nas fronteiras entre assuntos. Peço que registre um trecho da questão e uma razão curta para a escolha, podendo declarar dúvida. Em Q0205, a sugestão foi Parte Geral dos Recursos e a referência final ficou em Carta Testemunhável; essa distinção precisa orientar outros casos semelhantes. A discordância também pode revelar ambiguidade da árvore, não apenas erro de uma pessoa ou da máquina.

Na primeira tela de revisão, eu ocultei a sugestão para reduzir sua influência. Depois, reuni os desacordos para conferência. Nas 26 publicadas da amostra, houve acordo em 14 na revisão cega e em 25 após a conferência com as opções visíveis. Eu considero o segundo resultado promissor, mas não apago o primeiro nem prometo que já comprovamos 95% de precisão. Antes de ampliar a automação, recomendo estabilizar os critérios e fazer nova auditoria com amostra planejada. Ao longo do uso, eu reservaria seu tempo também para verificar publicações e reportes de alunos, e não apenas para esvaziar a fila de dúvidas.

## Referências e reprodução do experimento

Eu preservei dados, decisões, prompts e revisões em PIPILINE-GPT/entrega_final/execucao. Para repetir os cálculos locais, executo python reproduzir.py em entrega_final, com Python 3.10 ou superior. O comando reconstrói o CSV, verifica hashes, executa 13 testes e recalcula as métricas. Não executa nova inferência. Para novo lote, eu registraria novamente configuração do modelo, entradas, respostas, tempo e custo; não reutilizaria este calibrador como garantia de generalização.

[1] [Vício de uma Estudante. Case e anexos oficiais. Commit cc8e7eb7bd1069a57634a3e1136b3540c70abb77.](https://github.com/viciod/case-vicio-ia/tree/cc8e7eb7bd1069a57634a3e1136b3540c70abb77)

[2] [Guo et al. On Calibration of Modern Neural Networks. PMLR 70, 2017. Referência conceitual de calibração; meu estimador foi Beta por faixas, não temperature scaling.](https://proceedings.mlr.press/v70/guo17a.html)

[3] [NIST/SEMATECH. Confidence intervals. Fórmulas para proporções e limites de Wilson.](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)

[4] [El-Yaniv e Wiener. On the Foundations of Noise-free Selective Classification. JMLR 11, 2010.](https://www.jmlr.org/papers/v11/el-yaniv10a.html)

[5] [Databricks. Best practices for reliability. Referência para desenho futuro de ingestão e qualidade.](https://docs.databricks.com/aws/en/lakehouse-architecture/reliability/best-practices)

[6] [OpenAI. GPT-5.4 Mini. Preços consultados em 18/10/2026; cenário de produção não executado.](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
