# Fluxo executado

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


## Código e contratos

`sistema/preparar.py` trata e valida os dados; `referencia.py` normaliza a revisão inicial; `pipeline.py` reconstrói as rodadas, calibra e decide; `relatorio.py` gera uma árvore navegável e uma visão técnica histórica somente na área temporária. O relatório da entrega, na raiz, é a versão 3 revisada e não é substituído por esse gerador.

Os scripts de avaliação estão em `sistema/avaliacao/`: auditoria do sorteio, comparação cega e consolidação da adjudicação. Os 13 testes das regras ficam em `testes/test_pipeline.py`; três testes de organização protegem as entradas e a separação entre resultados e dados de reprodução.

Os módulos conservam os contratos de caminhos que utilizaram no experimento. `sistema/executar.py` monta esse layout apenas em área temporária, seguindo `sistema/mapa_reproducao.json`. Extrai os quatro anexos diretamente do ZIP original, sem manter uma segunda cópia deles no repositório. Dados tratados e métricas são reconstruídos. Só fontes, classificações GPT, revisões humanas e contratos congelados entram nessa montagem.

O score bruto e a confiança recalibrada são escalas distintas. O corte 0,80 é aplicado ao score, com alertas bloqueadores. Concordância por ancestralidade e exata são avaliadas separadamente; irmãos contam como erro e um extra correto não corrige o tema central.

Para outro lote, crie uma versão com nova inferência registrada e novo plano de avaliação. Os contratos atuais são do case de 359 questões; os parâmetros de confiança não devem ser transportados como garantia de qualidade para outra população.
