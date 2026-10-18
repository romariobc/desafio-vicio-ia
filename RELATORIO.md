<!-- Cópia textual do documento editável RELATORIO.docx, versão 3 revisada. -->

# Classificação de questões jurídicas com IA

## Resumo

Conduzi um agente GPT para transformar 359 questões e uma árvore de temas em decisões de publicar, revisar ou fora. Deleguei integralmente a execução técnica ao agente; orientei o trabalho, questionei resultados e defini encaminhamentos. Um advogado forneceu os pareceres humanos. O agente selecionou 316 questões, cobertura de 88,02%, e estimou precisão de 95,37%. Na amostra posterior, a concordância nas publicadas foi 53,85% na revisão cega e 96,15% após conferência humana com sugestões visíveis. Preservei os dois resultados e não considero comprovada a meta oficial. Entrego decisões, evidências, código e limites auditáveis.

## Como pensei antes do código

Interpretei o desafio como uma decisão de risco: publicar no tema errado prejudica o estudo; revisar consome tempo do professor; fora exige reconhecer uma lacuna da árvore. Meu objetivo foi ampliar a cobertura buscando pelo menos 95% de acerto nas publicadas e antecipar o resultado com uma previsão. Pela regra do case, tema exato e ancestral/descendente contam como acerto; irmãos contam como erro [1].

Parti da hipótese de que interpretar o conhecimento exigido pelo comando e pelas alternativas, confrontando caminhos completos da taxonomia, seria mais adequado que aceitar os metadados de origem. Adotei essa abordagem, mas não executei um teste controlado para medir sua superioridade. Reconheci que uma sugestão plausível e um score alto poderiam estar errados; por isso, incluí evidência textual, alertas e abstenção antes de ampliar a publicação.

## Minha atuação e as responsabilidades

Orientei o agente sobre contexto, objetivo, formato da entrega e experiência do avaliador. Questionei a execução, pedi avaliação cega e exigi preservar resultados e limitações. O agente realizou a leitura, escreveu e executou os scripts, propôs métodos e calculou métricas. As classificações usadas como referência foram fornecidas pelo avaliador humano.

A execução técnica foi realizada pelo agente GPT-6.1 Sol, com esforço de raciocínio médio, no Codex Desktop. A primeira rodada foi uma nova classificação pelas fontes, em uma conversa que já continha informações e resultados anteriores. Embora eu tenha orientado o agente a fundamentar cada decisão nas questões e na taxonomia, não considerei essa rodada independente do histórico. Posteriormente, organizei a avaliação humana cega, cuja interface ocultou as sugestões do modelo para reduzir sua influência nas escolhas do avaliador.

### Comunicação com o avaliador

Considerei a interação com o especialista parte da solução. Orientei o agente a criar microsites com uma questão por vez, busca na árvore, progresso e salvamento, evitando formulários extensos. Procurei deixar claro o que o avaliador precisava decidir e como registrar o parecer, concentrando seu esforço no julgamento jurídico. Essa escolha buscou facilitar a colaboração e produzir respostas utilizáveis; não medi redução de tempo ou satisfação.

## Objetivos e artefatos

Organizei o fluxo compreender → preparar → classificar → comparar → calibrar → avaliar sem sugestões → conferir divergências → entregar. Esperei como artefatos fontes com hashes, dados tratados, árvore ativa, decisões com evidências, prompts, referências humanas, política congelada, publicacao.csv, previsao.txt, testes, relatório e README. A falta do gabarito reservado da empresa não impediu a execução; estimar a precisão sem acessá-lo era parte do problema.

## Como operacionalizei o agente

### Dados e rodadas registradas

O agente preservou as fontes do commit cc8e7eb7bd1069a57634a3e1136b3540c70abb77, tratou HTML, entidades, Unicode e espaços e validou 359 questões e 377 temas, dos quais 375 ativos. Conservou originais e retirou os metadados de origem dos lotes de leitura. Na R1, leu as questões em 12 lotes e salvou tema, extras, conceito, evidência literal, alertas e score. A R2 foi comparação/calibração; na R3, registrou 15 ajustes, com 13 mudanças de tema central. Não foram três inferências completas independentes.

### Instruções operacionais e seu propósito

Abaixo sintetizo os critérios documentados em prompts.md; são reconstruções operacionais, não transcrições literais de todas as mensagens da conversa. Dei prioridade às restrições verificáveis, além da atribuição genérica de um papel de especialista.

Classificar: “Leia a questão integralmente e identifique o conhecimento necessário para responder. Compare os caminhos completos dos temas ativos. Registre tema central, extras, conceito, evidência literal, alertas e score subjetivo. Não tome os metadados de origem como gabarito.” Isso tornou as escolhas inspecionáveis e limitou saídas fora do contrato.

Comparar: “Preserve a R1. Reconstrua os pareceres em relação às sugestões originalmente revisadas. Um concordo não valida automaticamente uma nova classificação; uma rejeição sem correção não fornece outro rótulo.” Isso evitou inventar referência humana ou transferir aprovação entre modelos e rodadas.

Ajustar e avaliar: “Documente toda alteração e use apenas a partição de calibração para ajustar a política. Congele decisões e previsão antes de calcular a avaliação posterior. Preserve os desacordos.” Isso separou desenvolvimento e avaliação operacional, embora a exposição histórica e a seleção dirigida continuassem limitando a independência.

### Coleta e retorno dos pareceres

Separei a comunicação em dois momentos: na leitura cega, a tela ocultou a pré-classificação; na conferência, apresentou os desacordos e os caminhos dos temas, sem escolha pré-marcada. O avaliador podia manter sua decisão, adotar a sugestão, escolher outro tema ou registrar uma situação inconclusiva. Solicitei decisão associada à questão, tema válido e justificativa nos casos necessários.

A primeira exportação incompleta mostrou que simplicidade visual não garante dados utilizáveis. Conferi o preenchimento e foi necessário refazer a revisão. Tratei o episódio como problema do fluxo de coleta, sem atribuí-lo automaticamente ao avaliador. O agente registrou e comparou os pareceres; o julgamento continuou humano.

### Calibração e regra de publicação

Utilizei 60 pareceres anteriores, com 57 rótulos reconstruíveis e três rejeições sem alternativa. A seleção era dirigida, não uma amostra dimensionada para comprovar 95%. O agente separou 42 para calibração e 18 para avaliação operacional. Aceitei o risco de ancoragem da revisão inicial pelo prazo e pela experiência do revisor, registrando a limitação.

O agente distinguiu score subjetivo de probabilidade calibrada [2]. Em faixas abaixo de 0,80, de 0,80 a menos de 0,95 e a partir de 0,95, estimou q = (k + 1)/(n + 2), média posterior Beta(1,1). Assim, 10/10 resultaram em 11/12 = 91,67%; 26/26, em 27/28 = 96,43%. PAVA verificou a ordem das estimativas, sem precisar agrupar faixas. Essa suavização evita confiança de 100% com poucos exemplos; não garante generalização.

O corte escolhido foi 0,80 no score bruto: maior cobertura entre candidatos com concordância pontual ≥ 95% na calibração e mínimo de oito rótulos avaliáveis. Alertas bloquearam publicar; dúvidas seguiram para revisar com sugestão, e lacunas para fora. No CSV, a confiança é recalibrada, distinta da escala do corte.

## Diagnóstico experimentos e resultados

### Dificuldades e becos sem saída

O agente encontrou oito títulos repetidos e vinte descrições vazias. Em Q0024, a calibração expôs confusão entre nós próximos e levou a um ajuste documentado para o nível sociológico das teorias. Em Q0205, a sugestão final Parte Geral dos Recursos divergiu de Carta Testemunhável, situada em outro ramo: o contexto geral não bastou para identificar o instituto específico. Evidência literal e coerência semântica, sozinhas, não asseguram classificação jurídica correta.

Descartei aceitar origem, score alto, concordância entre rodadas ou promoção indiscriminada ao pai como provas de acerto. Não testei embeddings: similaridades próximas entre temas de fronteira são um risco previsto para produção. Na revisão humana, expertise, critérios da árvore e interface influenciam o julgamento; discordância não comprova falta de competência. A coleta incompleta reforçou a necessidade de conferir os registros, além de facilitar o uso das telas.

### Cobertura e previsão preservadas

O agente decidiu 316 publicar, 39 revisar e quatro fora. Cobertura = 316/359 = 88,02%; revisão = 10,86%; fora = 1,11%; abstenção total = 43/359 = 11,98%. A cobertura é exata neste lote, por isso seu intervalo é pontual. A previsão de precisão, 95,37%, veio da média das probabilidades recalibradas das publicadas. O intervalo original 90,36%–100% veio de Wilson sobre 36/36 na calibração após escolher o corte; é descritivo e otimista, não intervalo validado da generalização dessa média.

| Referência humana | Concordância nas publicadas | Wilson de 95% |
| --- | --- | --- |
| Guiada inicial — reservada operacional | 16/16 = 100% | 80,64%–100% |
| Cega — sem sugestão visível | 14/26 = 53,85% | 35,46%–71,24% |
| Guiada final — adjudicação com sugestões | 25/26 = 96,15% | 81,11%–99,32% |

O sorteio sem reposição selecionou 30/359 questões; 26 eram publicadas e quatro revisar. Três itens já estavam na calibração e não confirmei ausência de exposição prévia do avaliador. Das 15 divergências totais, o humano alterou 14; entre as publicadas, alterou 11 das 12. Mudou a referência, não o modelo. A conferência guiada não foi um novo teste cego nem permite estimar redução causal de ancoragem.

Na adjudicada, houve 22/26 = 84,62% de concordância exata e 25/26 = 96,15% por ramo. O resultado ficou +0,78 ponto percentual da previsão; a cega ficou 41,52 pontos abaixo dela. O Brier, média de (q − y)², caiu de 0,4133 para 0,0351 porque mudaram os rótulos humanos, sem nova calibração. Os intervalos Wilson usam k/n e z = 1,96 [3]; não corrigem ancoragem ou erro da referência. Mesmo 26/26 dariam limite inferior de 87,13%. Não considero comprovada a meta oficial de 95%.

## Produção para 50 mil questões semanais

### Da importação ao reporte do aluno

Eu receberia cada importação com versão, preservaria o original e validaria campos, IDs e duplicatas. Usaria hash para processar apenas itens novos ou alterados, com fila, concorrência limitada, controle de limites da API, retentativas e checkpoints. Cada decisão registraria versões de texto, árvore, prompt, modelo e calibrador. Publicaria em versão auditável, encaminharia dúvidas ao professor e manteria exclusões rastreáveis.

Usaria embeddings para recuperar candidatos somente após medir se o tema correto está entre eles, com fallback quando a recuperação falhar. Uma LLM interpretaria comando e alternativas e retornaria IDs ativos, evidência e alertas em formato validado. Com referência suficiente, compararia um classificador treinado à LLM em teste separado. Agentes poderiam coordenar tarefas e falhas; seu acordo não substituiria referência independente. A abstenção manteria o compromisso entre risco e cobertura [4].

Começaria com Python, armazenamento versionado, banco relacional e processamento em lote. Consideraria Databricks se já estivesse no ambiente ou houvesse múltiplas fontes a governar: bronze para bruto, silver para tratado e gold para validado [5]. Não o considero obrigatório pelo volume isolado. APIs, embeddings, classificador treinado e essa infraestrutura são propostas, não componentes executados neste case.

Planejaria auditorias semanais aleatórias das publicadas, além da revisão de casos difíceis e exclusões. Fixaria amostra e critérios antes dos resultados; monitoraria precisão por ramo e exata, intervalos, Brier, cobertura, custo, latência e fila. Separaria desenvolvimento, calibração e teste. Reportes de alunos abririam incidentes ligados à versão publicada: julgamento humano, correção, investigação de casos semelhantes e teste de regressão. Reduziria automação quando o risco excedesse o limite aprovado.

### Comunicação entre setores

Em produção, manteria um ciclo entre importação, tecnologia, professores e atendimento ao aluno. Cada encaminhamento ao especialista apresentaria a questão, o caminho sugerido e o motivo da revisão. O parecer retornaria estruturado, permitindo publicar, corrigir ou investigar a taxonomia. Reportes de alunos teriam contexto, responsável pelo encaminhamento e registro da resolução. Eu buscaria reduzir solicitações incompletas e tornar a colaboração entre setores compreensível e rastreável.

### Custo e capacidade operacional

Não medi custo marginal, tokens ou duração integral da inferência no aplicativo. Para uma futura API, o cenário GPT-5.4 Mini precisaria de avaliação própria. Com preços consultados em 18/10/2026 de US$ 0,75 por milhão de tokens de entrada e US$ 4,50 de saída [6], 1.500 tokens de entrada e 200 de saída custariam US$ 0,002025 por questão, US$ 101,25 por 50 mil. Com 12 mil de entrada, seriam US$ 0,0099 e US$ 495. Excluem infraestrutura, embeddings, retentativas, tributos e revisão humana; não são custos observados do GPT-6.1 Sol.

Mantida hipoteticamente a taxa de 39/359 para revisão, seriam cerca de 5.432 itens semanais; a dois minutos cada, 181 horas. Eu mediria o tempo real e priorizaria reduzir ambiguidades e retrabalho. O repositório permite executar python reproduzir.py com Python 3.10+: reconstrói dados e métricas, passa 13 testes e confere hashes; foi verificado em Windows e Linux. Isso reproduz checkpoints, sem executar nova inferência.

### Referências e artefatos para reprodução

[1] [Case oficial e anexos no commit fixado.](https://github.com/viciod/case-vicio-ia/tree/cc8e7eb7bd1069a57634a3e1136b3540c70abb77)

[2] [Guo et al. On Calibration of Modern Neural Networks. PMLR, 2017. Base conceitual; não apliquei temperature scaling.](https://proceedings.mlr.press/v70/guo17a.html)

[3] [NIST/SEMATECH. Confidence intervals. Método de Wilson.](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)

[4] [El-Yaniv e Wiener. On the Foundations of Noise-free Selective Classification. JMLR, 2010.](https://www.jmlr.org/papers/v11/el-yaniv10a.html)

[5] [Databricks. Best practices for reliability. Desenho futuro de ingestão e qualidade.](https://docs.databricks.com/aws/en/lakehouse-architecture/reliability/best-practices)

[6] [OpenAI. GPT-5.4 Mini. Tabela de preços do cenário proposto.](https://developers.openai.com/api/docs/models/gpt-5.4-mini)

[7] [Repositório da entrega: fontes, prompts, decisões, revisões, scripts e manifesto de reprodução.](https://github.com/romariobc/desafio-vicio-ia)

## Memo para o professor

Professor, organizei este experimento para que o aluno encontre questões do conhecimento que procura. Deleguei a classificação ao agente de IA e utilizei avaliação humana para examinar suas decisões. O agente pode interpretar bem o texto e ainda escolher um tema inadequado. Por isso, preciso de critérios jurídicos claros para orientar tanto a máquina quanto quem revisa.

### O que encontrei

A árvore contém nomes repetidos e descrições ausentes ou pouco discriminantes. Algumas questões mencionam um assunto no cenário, mas exigem outro conhecimento para responder. Outras atravessam assuntos vizinhos. Essas situações dificultam distinguir o tema central dos assuntos adicionais e podem levar a categorias genéricas que acumulam conteúdos diferentes.

Q0205 exemplifica uma diferença relevante: o agente sugeriu Parte Geral dos Recursos, enquanto a referência final indicou Carta Testemunhável. Esses temas estão em ramos distintos da árvore. O caso exige definir quando classificar pelo contexto geral e quando pelo recurso específico, para orientar futuras questões semelhantes.

### O que recomendo mudar nos temas

Recomendo manter identificadores estáveis e mostrar sempre o caminho completo do assunto. Para cada tema, peço uma definição curta, exemplos do que entra e do que não entra e orientações para distinguir temas vizinhos. Eu não uniria categorias apenas porque têm o mesmo nome. Antes de criar novos temas, examinaria as lacunas apontadas pelas questões fora. Também evitaria usar temas introdutórios como destino automático de toda dúvida.

### Como você pode contribuir

Precisamos da sua ajuda para definir qual assunto cada questão realmente cobra, principalmente quando ela envolve temas próximos ou mais de um conteúdo. Nesses casos, indique o tema principal e se vale acrescentar outro marcador. Um trecho da questão e uma explicação curta já ajudam a orientar futuras classificações. Se houver dúvida ou nenhum tema servir bem, registre isso também: essa informação ajuda a melhorar a árvore de assuntos.

Para facilitar a revisão, criamos duas telas. Na primeira, você escolhe o tema sem ver a sugestão da IA. Na segunda, confere apenas os casos em que as escolhas foram diferentes. Assim, buscamos concentrar seu tempo nas decisões que precisam de atenção.

No experimento, a IA e o avaliador escolheram temas compatíveis em 14 das 26 questões selecionadas para publicação. Depois da conferência, esse número passou para 25. Como algumas escolhas humanas mudaram ao ver as opções, esse resultado ainda precisa ser confirmado em uma nova avaliação.

Antes de ampliar a publicação automática, recomendamos esclarecer os critérios dos temas e revisar uma nova amostra. Depois, sua participação continuará importante para verificar parte das questões publicadas, resolver dúvidas e examinar problemas apontados pelos alunos. O sistema organiza as informações e registra as decisões; você contribui com o julgamento jurídico que orienta sua qualidade.
