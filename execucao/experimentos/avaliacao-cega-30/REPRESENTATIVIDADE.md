# Auditoria da amostra cega — antes da comparação de resultados

## Parecer

O sorteio das 30 questões é válido e reproduzível como amostragem aleatória simples sem reposição do lote de 359. Isso permite uma avaliação exploratória baseada em probabilidades de inclusão conhecidas. Não assegura uma miniatura proporcional de todas as disciplinas nem tamanho suficiente para demonstrar precisão mínima de 95%. O parecer foi obtido sem comparar rótulos humanos e automáticos.

## Verificação do desenho

- 30 IDs únicos; todos pertencem ao lote. A semente reproduz os mesmos IDs e a mesma ordem.
- Cada questão teve probabilidade de inclusão 30/359 = 8.36%.
- Questões não foram escolhidas em função de acertos observados. O sorteio não filtrou pela decisão/confiança do modelo.
- Fontes e registro do experimento conferidos; a exportação humana contém os mesmos 30 IDs.
- As proporções de disciplina abaixo são as propostas pelo pipeline, não rótulos humanos independentes.

## Composição por decisão

| Grupo | Lote | % lote | Amostra | % amostra |
|---|---:|---:|---:|---:|
| publicar | 316 | 88.02% | 26 | 86.67% |
| fora | 4 | 1.11% | 0 | 0.00% |
| revisar | 39 | 10.86% | 4 | 13.33% |

O foco do desafio é a precisão das publicadas: o denominador de avaliação correspondente é 26, não 30. Não há nenhuma das 4 exclusões na amostra. A ausência não invalida o sorteio: a chance de selecionar zero das quatro exclusões neste desenho é aproximadamente 70,43%. Entretanto, o experimento não audita essa fila.

## Composição por disciplina proposta

| Grupo | Lote | % lote | Amostra | % amostra |
|---|---:|---:|---:|---:|
| Processo Penal | 114 | 31.75% | 5 | 16.67% |
| Criminologia | 34 | 9.47% | 3 | 10.00% |
| Penal | 146 | 40.67% | 17 | 56.67% |
| Direito Penal - Legislação Especial | 61 | 16.99% | 5 | 16.67% |
| Sem tema (fora) | 4 | 1.11% | 0 | 0.00% |

Penal está sobrerrepresentado e Processo Penal sub-representado na amostra obtida. Isso pode ocorrer ao acaso num sorteio válido; não é prova de manipulação nem motivo para substituir questões após a avaliação. Os grupos pequenos não sustentam conclusões separadas por disciplina.

### Apenas as publicadas (população-alvo do requisito de precisão)

| Grupo | Lote | % lote | Amostra | % amostra |
|---|---:|---:|---:|---:|
| Processo Penal | 106 | 33.54% | 4 | 15.38% |
| Criminologia | 33 | 10.44% | 3 | 11.54% |
| Penal | 121 | 38.29% | 14 | 53.85% |
| Direito Penal - Legislação Especial | 56 | 17.72% | 5 | 19.23% |

As quatro publicadas de Processo Penal não bastam para uma conclusão robusta específica sobre essa disciplina. Não ajustar pesos depois de observar erros para obter um resultado melhor. Uma análise ponderada, se necessária, deverá ser especificada e reportada como análise adicional, incluindo sua maior incerteza.

## Independência e exposição prévia

Três IDs já tinham rótulos na calibração: Q0022, Q0041, Q0048. Não há sobreposição com os 18 do reservado anterior. Dos 30, 27 não pertenciam à revisão humana antiga. Q0141 recebeu ajuste semântico na R3; isso não significa que seu novo rótulo humano tenha sido visto antes.

Para auditoria do lote fixo, o sorteio continua válido mesmo incluindo itens usados no desenvolvimento. Para avaliar generalização em itens sem referência prévia, deve-se distinguir o subconjunto sem rótulos de desenvolvimento, que é outro alvo de inferência. Não chamar os 30 de conjunto totalmente novo e independente. O registro de exposição prévia está como não informado nas 30 respostas: a interface oculta sugestões, mas a memória do avaliador não está controlada.

## Tamanho e limite da evidência

Sem olhar os resultados, considere o melhor cenário possível: 26/26 publicadas corretas. O limite inferior Wilson bilateral de 95% seria cerca de 87,13%; o limite inferior exato binomial unilateral de 95% seria cerca de 89,12%. São métodos diferentes; nenhum provaria a meta mínima de 95%.

No lote finito de 316 publicadas, 16 erros já violariam a meta. Mesmo existindo esses 16 erros, a chance de um sorteio de 26 publicadas não encontrar nenhum seria 24.44%. Assim, zero erros na amostra ainda seria compatível com um lote abaixo da meta.

Como cenário de planejamento (não resultado ou exigência universal): 53 publicadas aleatórias, todas corretas, permitiriam rejeitar a hipótese de 16 ou mais erros no lote de 316 em teste exato unilateral de 5%; a cauda de 2,5% exigiria 64 sem erro. Se aparecer erro, os tamanhos mudam. Para novos lotes/modelo binomial, 59 sem erro é o cenário unilateral exato correspondente. O protocolo deve ser fixado antes de examinar os acertos; não acrescentar questões sucessivamente até um intervalo passar de 95%.

A margem normal aproximada de pior caso para a proporção geral com n=30 e N=359 é ±17.15 pontos percentuais, com correção finita. É apenas indicação da baixa resolução; não usar aproximação normal para o intervalo próximo de 100%.

## Completude dos arquivos recebidos

JSON/CSV foram localizados na raiz de PIPILINE-GPT. A exportação registra 30 respostas e IDs corretos, mas apenas 1/30 concluída: 28 marcadas como classificadas não têm tema escolhido e há uma marcação de fora sem justificativa. O usuário informou que verificará com o avaliador. Isso é uma pendência da coleta/exportação, independente da validade do sorteio. Não transformar ausências em acertos, erros ou abstenções do modelo.

## Procedimento recomendado

1. Preservar este sorteio, seus arquivos e a política de publicação congelada.
2. Obter a exportação completa e confirmar exposição prévia do avaliador.
3. Comparar as publicadas com a nova referência, reportando n avaliável, acerto exato, acerto por ramo e incerteza; tratar revisar separadamente.
4. Usar os 30 como auditoria inicial, sem proclamar certificação de 95%.
5. Se for necessária evidência mais forte, definir antes dos resultados um plano adicional com tamanho, alvo e regra de parada fixos. Amostragem estratificada pode melhorar cobertura de disciplinas; revisar as exclusões deve ser outra componente identificada.

## Referências

- Statistics Canada, [Probability sampling](https://www150.statcan.gc.ca/n1/edu/power-pouvoir/ch13/prob/5214899-eng.htm): seleção probabilística, amostragem simples e cobertura de subgrupos.
- NIST, [Exact binomial confidence limits](https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbici.htm): intervalos exatos e cautela com amostras pequenas/raridade de falhas.
- Os cálculos do lote finito usam P(X=0)=C(N-D,n)/C(N,n), distribuição hipergeométrica. Script e contagens estão ao lado deste relatório.
