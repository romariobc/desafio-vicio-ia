# Verificação da revisão cega refeita

## Integridade

30 respostas concluídas, IDs correspondentes ao sorteio original, temas ativos e consistência entre CSV/JSON. São 29 classificações na árvore e 1 fora com justificativa. O arquivo foi exportado em 2026-10-18T14:04:13.685Z (UTC). A classificação congelada do modelo permaneceu íntegra.

Identificação do avaliador não preenchida; exposição prévia não informada nas 30 respostas. Portanto, cegamento da interface é verificável, mas experiência prévia e autoria não estão documentadas no arquivo. Os problemas de tamanho/composição da amostra permanecem descritos em ../REPRESENTATIVIDADE.md.

## Resultado bruto — regra de ancestralidade do desafio

| Subconjunto | Acertos por ramo | Acertos exatos |
|---|---:|---:|
| Todas as 30 | 15/30 (50.00%) | 11/30 |
| Publicadas | 14/26 (53.85%) | 11/26 |
| Revisar | 1/4 | 0/4 |

As 12 divergências nas publicadas contam contra a referência recebida. Extras não corrigem central errado; irmãos e nós homônimos em ramos diferentes não são equivalentes. Nenhum ID foi remapeado automaticamente para melhorar o resultado.

Intervalo Wilson bilateral descritivo nas publicadas: 35.46%–71.24%. A cobertura da entrega permanece 316/359 = 88.02%; cobertura não é precisão.

Previsão original: 95.37%. Observado contra esta referência nas publicadas: 53.85%. Diferença: 41.52 pontos percentuais. A meta pontual de 95% não foi atingida neste experimento. Esta evidência contradiz o desempenho sugerido pela referência antiga e precisa ser apresentada, não ocultada.

## Divergências que pedem adjudicação

Há escolhas de referência que suscitam dúvida semântica. Por exemplo, Q0239 apresenta alternativas sobre cálculo/dosimetria da pena, mas recebeu tema de teorias sociológicas da criminalidade; Q0100 trata de uma situação sexual com menor e recebeu Difamação. São sinais para conferir a seleção no formulário e os critérios jurídicos; não constituem prova de que o revisor errou. Outras diferenças envolvem foco da questão (conceito geral, tipo específico ou contexto do caso) e fronteiras da árvore.

Preservar os rótulos recebidos. Se o avaliador corrigir algum, obter ID, rótulo anterior, novo rótulo, justificativa e autoria em outra versão. Não usar a própria LLM como árbitro final para transformar suas discordâncias em acertos.

| Questão | Decisão | Tema do modelo | Tema humano |
|---|---|---|---|
| Q0239 | revisar | 5199 — Penal > Teoria da Pena | 4387 — Criminologia > Teorias Sociológicas Explicativas da Criminalidade > Teorias de Nível Sociológico |
| Q0064 | publicar | 5165 — Penal > Dos Crimes Contra o Patrimônio > Apropriação indébita | fora — fora |
| Q0077 | revisar | 5171 — Penal > Introdução ao Estudo do Direito Penal > Conceito e Fontes do Direito Penal | 6727 — Penal > Teoria da Pena (Parte 2) |
| Q0205 | publicar | 5512 — Processo Penal > Parte Geral dos Recursos | 5567 — Processo Penal > Recursos em Espécies > Carta Testemunhavel |
| Q0100 | publicar | 5103 — Penal > Dos Crimes Contra a Dignidade Sexual > Estupro e Estupro de Vulnerável | 5123 — Penal > Dos Crimes Contra a Honra > Difamação |
| Q0141 | publicar | 4387 — Criminologia > Teorias Sociológicas Explicativas da Criminalidade > Teorias de Nível Sociológico | 4380 — Criminologia > Teoria Geral da Criminologia |
| Q0161 | publicar | 5588 — Processo Penal > Teoria Geral das Prisões > Relaxamento da Prisão | 5498 — Processo Penal > Inquérito Policial |
| Q0058 | publicar | 4378 — Criminologia > Processos de Criminalização e Cifras Criminais > Criminalização Primária e Secundária | 4380 — Criminologia > Teoria Geral da Criminologia |
| Q0252 | publicar | 5199 — Penal > Teoria da Pena | 6738 — Processo Penal > Sentença Penal (Parte 2) |
| Q0093 | publicar | 5223 — Penal > Teoria do Crime: Fato Típico > Crimes Omissivos e Comissivos | 5149 — Penal > Dos Crimes Contra a Vida |
| Q0074 | publicar | 5181 — Penal > Lei Penal no Tempo e no Espaço > Lei penal no Tempo | 5170 — Penal > Introdução ao Estudo do Direito Penal |
| Q0048 | publicar | 5193 — Penal > Punibilidade > Anistia, Graça e Indulto | 6726 — Penal > Teoria da Pena (Parte 1) |
| Q0353 | revisar | 5535 — Processo Penal > Procedimento Ordinário > Audiência de Instrução e Julgamento | 5490 — Processo Penal > Das Questões e Processos Incidentes |
| Q0092 | publicar | 5511 — Processo Penal > Nulidades > Nulidades em Espécie | 5480 — Processo Penal > Competência |
| Q0041 | publicar | 5184 — Penal > Medida de Segurança | 6726 — Penal > Teoria da Pena (Parte 1) |

## Próximo passo

Conferir com o avaliador as divergências e preencher identificação/exposição prévia. Manter separadas a comparação original e eventual comparação adjudicada. Se houver novos ajustes do classificador usando estes resultados, esta amostra passa a integrar desenvolvimento; a próxima avaliação deverá ser outra amostra planejada antes dos resultados. Nenhum ajuste ou nova classificação foi executado nesta verificação.
