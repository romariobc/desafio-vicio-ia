# Plano da execução GPT — registrado antes da nova classificação

Data: 18/10/2026. Fonte: commit `cc8e7eb7bd1069a57634a3e1136b3540c70abb77` de https://github.com/viciod/case-vicio-ia.

## Escopo e autoria

Recomeçar com os anexos originais, sem importar as classificações antigas. A inferência semântica será realizada pelo assistente GPT da sessão Codex, registrada por questão em arquivos de texto versionáveis. Não há chamada externa Gemini/OpenAI nos scripts. Os scripts reproduzem a transformação das decisões registradas em artefatos; uma nova inferência exige nova análise do assistente. O identificador comercial exato, os tokens faturados e o custo marginal da inferência não estão disponíveis. Não alegar reprodução bit a bit de uma nova inferência.

O contexto desta conversa contém decisões e estatísticas anteriores; portanto a rodada inicial nova é uma reanálise, NÃO um experimento cego. Não copiar respostas anteriores e não usar metadados de origem como rótulos.

## Rodadas

1. R1: ler questões completas e árvore ativa; registrar tema central, extras, conceito, evidência literal, score subjetivo e alertas. A pontuação não é precisão medida.
2. R2: importar literalmente a revisão humana autorizada, reconstruindo os rótulos a partir da sugestão ORIGINAL registrada nela. Separar deterministicamente calibração e avaliação (semente 20261018, por veredito e estrato registrado, aproximadamente 2/3 e 1/3). Discordância sem tema corrigido é restrição negativa, NÃO um rótulo inventado. Comparar R1 com os rótulos reconstruídos; usar somente a partição de calibração para aprender ajustes e a política.
3. R3: reanalisar os casos problemáticos à luz dos erros de calibração e aplicar regras documentadas. Não converter automaticamente extras em ambiguidade. Manter sugestão específica quando justificável; promover ao pai somente com justificativa semântica registrada. Preservar todo score bruto. Ajustar confiança por bins fixos do score e modelo Beta(1,1): média posterior (acertos+1)/(n+2), sem chamar isso de garantia. Escolher uma única política entre cortes predefinidos para maximizar cobertura com acerto empírico >=95% na calibração e pelo menos 8 publicadas avaliáveis. Se não houver corte, não inventar meta atingida. Avaliar uma vez na partição reservada; não retunar após vê-la.

## Score da R1

Score de certeza do assistente entre 0 e 1, subjetivo, considerando evidência textual, correspondência com caminho da taxonomia, foco da questão e integridade do texto. Para tornar a justificativa auditável: registrar conceito cobrado, trecho literal, alertas de ambiguidade/mosaico/incompletude e tema escolhido. Valores próximos de 1 não são probabilidades calibradas. Bins de calibração fixos: baixo <0.80; médio [0.80,0.95); alto >=0.95. Não usar concordância entre rodadas como prova de acerto.

## Riscos explicitamente aceitos

- O usuário aceita ancoragem: revisão assistida pelas sugestões anteriores, por prazo curto, otimização do tempo e experiência do revisor humano. Isso é aceitação de uma limitação, não remoção do viés.
- A revisão é referência operacional parcial, não os rótulos oficiais reservados pela empresa.
- Seleção original dos 60 IDs não tem probabilidades de inclusão conhecidas. Não atribuir margem de erro de amostra aleatória nem extrapolar automaticamente a precisão ao lote.
- A separação nesta execução evita reutilização direta dos rótulos reservados pelos algoritmos, mas não apaga a exposição histórica nesta conversa.
- Intervalos Wilson serão descritivos/condicionais; não provarão generalização nem corrigirão seleção e ancoragem.

## Métricas e parada

Precisão nas publicadas avaliáveis = acertos por ancestralidade / publicadas com referência positiva conhecida. Reportar também acerto exato, Brier, n, desconhecidos e erros conhecidos sem rótulo alternativo. Cobertura = publicar/359; abstenção total = (revisar+fora)/359; fila humana = revisar/359; exclusão = fora/359. Cobertura do lote é exata, sem intervalo artificial para novos lotes.

Executar as três etapas e uma avaliação final; não repetir ajustes até fazer o teste passar. Atingir >=95% na referência é resultado local, não comprovação da régua oficial. Se a evidência não sustentar a meta, registrar a limitação e a revisão adicional necessária.

## Referências metodológicas

- Contrato do desafio: PDF original, p. 2 e LEIA-ME dos anexos.
- Guo et al. (2017), calibração de probabilidades: https://proceedings.mlr.press/v70/guo17a.html (fundamento; não implementamos temperature scaling sem logits).
- El-Yaniv e Wiener (2010), classificação seletiva e risco/cobertura: https://www.jmlr.org/papers/v11/el-yaniv10a.html.
- scikit-learn, prevenção de vazamento entre desenvolvimento e teste: https://scikit-learn.org/stable/common_pitfalls.html.
