# Case Vício — classificação hierárquica com GPT e abstenção

Execução de 18/10/2026. Fontes do [repositório oficial](https://github.com/viciod/case-vicio-ia/tree/cc8e7eb7bd1069a57634a3e1136b3540c70abb77), commit fixado e conteúdo verificado por hash. Relatório conciso organizado em cinco partes, incluindo memo.

## 1. Problema, hipóteses e execução

O aluno procura um tópico e recebe questões. O erro de publicação custa aprendizado incorreto; revisão custa tempo do professor. O desafio pede maximizar cobertura respeitando pelo menos 95% de acerto nas publicadas. Acerto é tema exato ou ancestral/descendente, nunca irmão. Os rótulos oficiais existem, mas são reservados pela empresa; não foram acessados.

Hipótese inicial: uma LLM interpreta melhor o conteúdo do que metadados de origem, mas sua confiança subjetiva não basta para decidir publicação. O GPT da sessão leu as 359 questões completas em 12 lotes, usando a árvore ativa, e registrou tema, conceito, evidência literal, score e alertas por questão. Não usamos nem executamos Gemini. Código Python trata os dados, valida e reproduz o pós-processamento; as decisões de inferência estão nos arquivos PSV. Identificador comercial exato e tokens faturados não foram expostos pelo ambiente.

O plano foi registrado antes da nova R1. A R1 foi congelada antes da importação normalizada da referência. A sessão contém histórico anterior: esta é uma reanálise com exposição prévia, não inferência cega. R1: classificação nova. R2: confronto com referência e calibração. R3: reclassificação seletiva documentada, preservando os demais registros e aplicando a política ao lote completo; não é uma nova inferência independente de 359 itens.

Descartamos metadados como rótulos, confiança >=0,98 como suposta prova de precisão, fusão automática de homônimos e promoção ao pai pela mera presença de extras. Também descartamos ajustar repetidamente após olhar a avaliação reservada. Score inicial é subjetivo; calibração estima acerto com dados de referência, distinção discutida por [Guo et al.](https://proceedings.mlr.press/v70/guo17a.html). A possibilidade de abster-se é a base do compromisso risco/cobertura de [El-Yaniv e Wiener](https://www.jmlr.org/papers/v11/el-yaniv10a.html).

## 2. Dados, diagnóstico e referência

São 359 IDs únicos e 377 temas, dos quais 375 ativos e 2 inativos (5078 e 5234). A preparação valida unicidade, parentesco, níveis e ciclos; preserva fontes, HTML e IDs; converte entidades/HTML em texto e normaliza NFC e espaços. A árvore não recebeu definições jurídicas inventadas. Há oito títulos repetidos e 20 descrições vazias. Muitas descrições restantes só repetem a hierarquia e a contagem no sistema de origem: não são definições de inclusão/exclusão.

Problemas relevantes: comandos genéricos; metadados errados; homônimos entre disciplinas; questões com vários subtemas; mosaicos entre ramos e contexto incompleto. Q0219 menciona participação necessária sem fornecer a situação antecedente e fica em revisão. Q0020 reúne temas sem um foco único e não é liberada só porque a raiz Penal contém tudo. Q0298 cobra relações de consumo na Lei 8137, enquanto o nó disponível diz especificamente CDC; não tratamos os dois como equivalentes.

A revisão anterior tem 60 pareceres: 54 concordâncias, 3 concordâncias no pai e 3 discordâncias sem tema corrigido. Reconstruímos os 57 rótulos positivos pelos IDs ANTIGOS mostrados ao revisor. Q0028, Q0053 e Q0168 fornecem restrições negativas, não um gabarito alternativo. Quando a nova sugestão repete o ID rejeitado, o erro conhecido entra no denominador específico; não é descartado para inflar precisão.

**Ancoragem aceita pelo usuário:** prazo curto, otimização do tempo e experiência do revisor. Esse motivo foi registrado, mas não elimina o viés. Identidade/credenciais e duração da revisão não são comprovadas pelo JSON. A seleção original é dirigida, sem probabilidades de inclusão conhecidas. Uma partição determinística gerou 42 pareceres para calibração e 18 reservados; a separação operacional segue o cuidado com vazamento descrito na [documentação do scikit-learn](https://scikit-learn.org/stable/common_pitfalls.html), sem alegar que recupera um teste cego após a exposição histórica.

## 3. Ajustes, confiança e resultados

Na calibração, R1 confundiu 4388 (Teorias Criminológicas em Espécie) com o irmão 4387 (Teorias de Nível Sociológico) em Q0024 e Q0031. A R3 corrigiu esses casos e outros de mesmo conceito sociológico, com justificativa por ID. Revisou ainda dolo geral, prisão domiciliar na execução e fraude patrimonial. Existem 15 registros de ajustes, dos quais 13 mudam o tema central. Q0053 e Q0168 receberam sugestão conservadora, mas continuam em revisão por referência inconclusiva.

Confiança: faixas fixas do score (<0,80; 0,80–0,9499; >=0,95), com média posterior Beta(1,1), (acertos+1)/(n+2), e agrupamento monotônico PAVA quando necessário. Não se trata de temperature scaling, fine-tuning ou comprovação de probabilidades individuais. Na calibração R3, as faixas média/alta tiveram 10/10 e 26/26 acertos e estimativas suavizadas de 0,9167 e 0,9643; a faixa baixa não tem rótulos centrais e usa apenas o prior 0,5, devendo ser retida. O score bruto é preservado em paralelo.

A política compara cortes predefinidos, exige >=95% de acerto pontual e pelo menos 8 publicadas avaliáveis na calibração, bloqueia mosaicos, raízes genéricas, texto insuficiente e referência inconclusiva, e maximiza a cobertura. O corte escolhido foi 0.80 no SCORE BRUTO; a coluna de confiança final usa outra escala, recalibrada. O critério de 8 é operacional, não demonstra poder estatístico. A política foi congelada antes de calcular as métricas reservadas.

| Medida | R1 preliminar | R3 final |
|---|---:|---:|
| Publicar | 246 | 316 |
| Revisar | 108 | 39 |
| Fora | 5 | 4 |
| Cobertura no lote | 68.52% | 88.02% |
| Abstenção (revisar + fora) | 31.48% | 11.98% |
| Precisão nas publicadas avaliáveis da calibração, incluindo rejeições conhecidas | 24/27 (88.89%) | 36/36 (100.00%) |
| Precisão nas publicadas da avaliação reservada | 14/14 (100.00%) | 16/16 (100.00%) |

R3: intervalo Wilson descritivo das publicadas reservadas **80.64%–100.00%**; acerto EXATO nesse subconjunto: 15/16. Considerando os 57 rótulos completos, o acerto por ramo é 57/57; nas publicadas com esses rótulos é 52/52. Estes últimos números incluem desenvolvimento e não são teste independente.

Brier no mesmo conjunto reservado de 17 predições com tema central: 0.016971 na R1 e 0.016573 na R3; menor é melhor. Não comparamos Brier de subconjuntos publicados diferentes como se fossem a mesma população. A faixa baixa permanece pouco informativa. A previsão congelada baseada na calibração é 95.37% de precisão, com cobertura exata de 88.02%. Os intervalos da previsão usam a calibração e são otimistas após seleção do corte; não são garantia estatística.

**Conclusão da avaliação:** a meta pontual foi atingida na referência reservada disponível; a precisão mínima de 95% no lote/gabarito oficial **não está comprovada**. Dezesseis acertos não justificam afirmar certeza sobre os outros itens. Não repetimos o ajuste até o teste passar. Como dimensão aproximada, 73 acertos em 73 amostras independentes produzem limite inferior Wilson de cerca de 95%; ainda seriam necessários amostragem adequada e controle dos vieses.

## 4. Produção, custo e operação

Para 50 mil questões semanais: validar importação e HTML; versionar taxonomia; obter candidatos por embeddings quando houver ganho medido contra árvore completa; usar LLM com saída estruturada; validar IDs/evidência; decidir por política congelada; encaminhar incerteza ao especialista. Um classificador supervisionado leve passa a fazer sentido após formar rótulos confiáveis. Agentes podem organizar etapas e curadoria; sua concordância não substitui referência. Nenhum desses componentes de produção foi implantado aqui.

Monitorar precisão por disciplina e por coorte, cobertura/abstenção, tempo de revisão, erros entre irmãos, lacunas e reportes de alunos; sortear auditorias também entre publicadas e fora. Separar dados para ajuste e avaliação, adjudicar divergências e reavaliar após mudanças da taxonomia. Guardar versões de modelo/prompt/entradas, latência, tokens e custos. Usar uma nova amostra independente para validar a política antes de operação real.

Nesta execução não houve API externa: custo incremental monetário e tokens não foram medidos; não são zero comprovado. O comando de reprodução mede somente o processamento local, excluindo inferência do assistente. Para orçar API em produção: custo/questão = tokens_entrada × preço_entrada/1 milhão + tokens_saída × preço_saída/1 milhão. **Simulação hipotética, não cotação nem medição:** preços de US$1/US$5 por milhão e 200 tokens de saída dariam US$0,0025 por questão com 1.500 tokens de entrada (US$125/50 mil), ou US$0,013 com 12.000 (US$650/50 mil), antes de retries, reanálise e revisão humana. Trocar pelas tarifas/tokens reais ao escolher fornecedor. Repetir a taxonomia pode dominar o custo; cache/batch/retrieval exigem teste e instrumentação, não foram usados aqui.

## 5. Memo para o professor

Professor(a), organizamos o lote para que o aluno receba questões relacionadas ao tópico que escolheu. Há **316 propostas de publicação**, **39 para revisão** e **4 fora por lacuna ou por matéria externa**. O resultado da pequena referência disponível é favorável, mas não garante o mesmo acerto nas demais questões.

Encontramos títulos repetidos em caminhos diferentes, tópicos sem descrição e perguntas que misturam assuntos. Pedimos critérios de inclusão/exclusão para homônimos, em especial as teorias criminológicas e a legislação especial. Recomendamos examinar as 20 descrições vazias, sem apagar IDs históricos automaticamente. A árvore original foi preservada.

Prioridades de curadoria: confirmar o enquadramento dos crimes esportivos de Q0168; decidir onde acolher o rito dos crimes funcionais de Q0017 e o cartel de Q0039; recuperar o contexto de Q0219; e estabelecer uma regra pedagógica para questões mosaico. Em Q0028 e Q0053 há sugestão no pai, mas a discordância antiga não validou um substituto, por isso permanecem em revisão.

O microsite anterior mostrou a sugestão ao revisor para economizar tempo; essa limitação foi aceita e registrada. Para validar a próxima versão, precisamos de uma auditoria nova de publicadas, com análise inicial sem sugestão, e de identificação do revisor e do critério adotado. Separar esclarecimento da taxonomia de decisão sobre cada questão evita corrigir o tópico errado por uma palavra do cenário.
