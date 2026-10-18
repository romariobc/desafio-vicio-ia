# Resultados e referências humanas

| Referência | Condição | Concordância nas publicadas | Wilson de 95% |
|---|---|---:|---:|
| Inicial, reservada operacional | Humana guiada por pré-classificação anterior | 16/16 = 100% | 80,64%–100% |
| Cega, 30 sorteadas | Sem sugestão visível; 26 publicadas | 14/26 = 53,85% | 35,46%–71,24% |
| Adjudicada | Conferência humana com sugestões visíveis | 25/26 = 96,15% | 81,11%–99,32% |

O lote contém 316 publicar, 39 revisar e quatro fora: cobertura de 88,02%. A previsão congelada é 95,37%, com intervalo original 90,36%–100%, descritivo e otimista após seleção de corte na calibração.

As classificações e probabilidades do modelo não mudaram depois do congelamento. Na adjudicação, o avaliador alterou 14 dos 15 desacordos, 11 entre os 12 das publicadas. Mudou a referência humana, não o modelo. O acerto exato final é 22/26; por ramo, 25/26. Q0205 permanece divergente.

Não se comprovou precisão oficial mínima de 95%. A amostra é pequena, três itens já pertenciam à calibração e a adjudicação não é teste cego independente. Os intervalos não corrigem ancoragem nem erro da referência. Não se quantificou causalmente redução de ancoragem.

## Localização das evidências

- `referencia_inicial/respostas.json`: 60 pareceres anteriores, 57 rótulos reconstruíveis e três rejeições sem alternativa; seleção dirigida, partição 42/18.
- `avaliacao_cega/respostas.json` e `.csv`: exportação cega completa recebida, preservada byte a byte.
- `adjudicacao/respostas.json` e `.csv`: conferência das divergências, preservada byte a byte.
- `resultados/`: métricas das duas referências e comparação por questão.
- `PLANO_INICIAL.md`: plano histórico anterior aos experimentos posteriores.

O sorteio, as comparações e os limites amostrais são recalculados por `python reproduzir.py`; as novas saídas aparecem em `saidas/avaliacoes/`. A história anterior permanece nos commits Git e na cópia local de segurança.
