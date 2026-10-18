# Escala e manutenção

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
