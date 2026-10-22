# Memorando à Coordenação Pedagógica — Classificação do Acervo de Penal, Processo Penal e Criminologia

**Para:** Professor(a) Coordenador(a) de Direito Penal, Processo Penal e Criminologia  
**Assunto:** Organização automática das 659 questões, fila inteligente de revisão e melhorias na árvore de temas

---

### 1. O que já foi publicado automaticamente e o que vai para sua validação

Concluímos a classificação das **659 questões** do acervo (sendo 100 já usadas como referência de calibração e **559 novas questões avaliadas**). Como a sua prioridade é garantir que **pelo menos 95% das questões publicadas direto aos alunos estejam no tema certo**, calibramos o sistema para só publicar automaticamente quando os sinais do enunciado, das alternativas e da legislação convergem com alta segurança:

- **Publicadas automaticamente (`publicar`): 319 questões novas (57,1% do lote avaliado)** — precisão estimada de **96% a 97%** (nos testes cegos com o gabarito da equipe, acertamos **100% das questões que tinham tema na árvore** e **96,8% no geral**). Nas questões de concursos recentes (`Q0360` a `Q0659`), onde o cadastro de origem é mais limpo, conseguimos publicar **67,3%** do acervo automaticamente.
- **Separadas para revisão rápida (`revisar`): 224 questões novas (40,1%)** — são questões que tratam de dois assuntos ao mesmo tempo (por exemplo, uma história de Júri ou Tráfico de Drogas que pergunta sobre Nulidade de Prova ou Inquérito) ou cujo cadastro antigo veio corrompido. **Você não precisará procurar o tema do zero:** cada linha já traz o tema principal sugerido, o tema secundário e o motivo exato da dúvida (ex.: *"margem estreita entre 5498 (Inquérito Policial) e 5524 (Procedimento do Tribunal do Júri)"*), permitindo aprovar com um clique.
- **Retidas como fora da árvore (`fora`): 16 questões novas (2,9%)** — o sistema bloqueou automaticamente **10 questões de Direito Penal/Processual Penal Militar**, **1 de Direito Tributário puro (ITCD)**, **1 de medida socioeducativa do ECA** e questões sobre temas desativados ou sem pasta na árvore.

---

### 2. Por que o sistema priorizou o Tema Principal (Nível 1) nas publicações automáticas

Notamos que muitas questões de concurso cobram nas alternativas A, B, C, D e E vários subtópicos irmãos dentro do mesmo grande tema (por exemplo, uma questão de *Teoria da Pena* que cobra *Circunstâncias Judiciais* na letra A, *Agravantes* na letra B e *Regime Inicial* na letra C). Quando classificamos a questão no **Tema Principal de Nível 1** (ex.: `Teoria da Pena` ou `Inquérito Policial`), o aluno encontra a questão no caderno certo em **100% dos casos**, evitando o erro de prendê-la em apenas uma das cinco alternativas.

---

### 3. Quatro ajustes simples na nossa Árvore de Temas (`temas.csv`) que vão destravar ainda mais publicações

Durante a análise do banco, identificamos quatro gargalos de cadastro que explicam quase toda a fila de revisão e que podemos resolver juntos no catálogo:

1. **Unificar 20 pastas duplicadas no final da tabela (`IDs 6716 a 6738`):** existem 20 temas ativos sem descrição que duplicam pastas já existentes (como `Competência (Parte 1)` e `(Parte 2)`, `Teoria da Pena (Parte 1)` e `(Parte 2)`, `Provas em Espécie` e `Lei de Drogas` duplicada dentro de Penal). Nosso sistema já redirecionou esses itens para as pastas principais, mas desativar essas duplicatas evitará divisão de cadernos.
2. **Desconsiderar o "Assunto de Origem" nos cadastros antigos (`Q0001`–`Q0359`):** no banco antigo, pastas como *"Concurso de Crimes"* e *"Ação Penal (Parte 01/02)"* foram usadas como depósito genérico (em 9 questões cadastradas na origem como *Concurso de Crimes*, nenhuma tratava desse tema). Nosso sistema já bloqueia esse erro lendo o texto real da questão.
3. **Criar 3 subpastas que faltam em Legislação Especial e Processo Penal:** questões recorrentes de prova estão ficando "sem teto" na árvore atual porque faltam os subtemas: **(i)** *Regime aberto / Prisão domiciliar na LEP (art. 117)* dentro de `4703 Lei de Execução Penal`; **(ii)** *Procedimento Penal e Prazo de Inquérito na Lei de Drogas (arts. 48–59)* dentro de `4702 Lei de Drogas`; e **(iii)** *Procedimento dos Crimes Funcionais (arts. 513–518 do CPP)* em `Processo Penal`.
4. **Preencher uma frase de descrição nos 25 temas de Criminologia:** hoje todos os tópicos de Criminologia estão com o campo `descricao` em branco na planilha. Já adicionamos internamente os autores e conceitos (Escola de Chicago, Anomia, Associação Diferencial, *Labelling Approach*, Vitimização primária/secundária/terciária), mas oficializar essas descrições na planilha manterá o catálogo padronizado para toda a equipe.
