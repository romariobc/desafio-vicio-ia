# Memorando à Coordenação Pedagógica — Classificação do Acervo de Penal, Processo Penal e Criminologia

**Para:** Professor(a) Coordenador(a) de Direito Penal, Processo Penal e Criminologia  
**Assunto:** Organização automática das 659 questões, fila inteligente de revisão e melhorias na árvore de temas

---

### 1. O que foi publicado automaticamente e o que separamos para sua validação

Concluímos a classificação das **659 questões** do acervo (sendo 100 já usadas como referência de calibração e **559 novas questões avaliadas**). Como a sua prioridade é garantir que **pelo menos 95% das questões publicadas direto aos alunos estejam no tema certo**, configuramos o sistema para só publicar automaticamente quando pelo menos dois sinais distintos (enunciado/alternativas, legislação citada e rubrica válida de edital) convergem com alta confiança:

- **Publicadas automaticamente (`publicar`): 302 questões novas (54,0% do lote avaliado)** — precisão prevista de **95%** (nos testes de validação com o gabarito da equipe, acertamos **60 de 62 publicadas = 96,8%**, sendo **100% nas questões que possuíam tema válido na árvore**, com intervalo estatístico de confiança de **89% a 99%** devido ao tamanho da amostra de 100 itens). Nas questões de concursos recentes (`Q0360` a `Q0659`), onde o cadastro de origem é mais organizado, publicamos **64,3%** (`193/300`) automaticamente, contra **42,1%** (`109/259`) no banco antigo.
- **Separadas para revisão rápida (`revisar`): 241 questões novas (43,1%)** — são questões que cobrem dois assuntos ao mesmo tempo (por exemplo, um caso de Júri ou Tráfico de Drogas que pergunta sobre Nulidade de Prova ou Inquérito) ou cujo cadastro antigo veio corrompido. **Você não precisará procurar o tema do zero:** cada linha já traz o tema principal sugerido, o tema secundário e o motivo exato da dúvida (ex.: *"margem estreita entre 5498 (Inquérito Policial) e 5524 (Procedimento do Tribunal do Júri)"*), permitindo decidir em poucos segundos.
- **Retidas como fora da árvore (`fora`): 16 questões novas (2,9%)** — o sistema bloqueou automaticamente **10 questões de Direito Penal/Processual Penal Militar**, **1 de Direito Tributário puro (ITCD)**, **1 de medida socioeducativa do ECA** e questões sobre temas desativados ou sem pasta na árvore.

---

### 2. Trade-off pedagógico: por que publicamos no Tema Principal (Nível 1)

Muitas questões de concurso cobram nas alternativas A, B, C, D e E vários subtópicos irmãos dentro do mesmo grande tema (por exemplo, uma questão de *Teoria da Pena* que cobra *Circunstâncias Judiciais* na letra A, *Agravantes* na letra B e *Regime Inicial* na letra C). Classificando a questão no **Tema Principal de Nível 1** (ex.: `Teoria da Pena` ou `Inquérito Policial`), garantimos pela regra oficial que o aluno encontre a questão no caderno correto sem o risco de prendê-la em apenas uma das cinco alternativas. Como contrapartida, perde-se a divisão fina por subtema na publicação automática — mas o sistema já deixa calculado internamente o subtema específico mais próximo caso queiramos exibi-lo como subtag complementar na plataforma.

---

### 3. Quatro ajustes simples na nossa Árvore de Temas (`temas.csv`) que vão reduzir a fila de revisão

Identificamos quatro problemas de cadastro na planilha `temas.csv` que explicam grande parte da fila de revisão e que podemos resolver juntos:

1. **Unificar 20 pastas duplicadas no final da tabela (`IDs 6716 a 6738`):** existem 20 temas ativos sem descrição que duplicam pastas já existentes (como `Competência (Parte 1)` e `(Parte 2)`, `Teoria da Pena (Parte 1)` e `(Parte 2)`, `Provas em Espécie` e `Lei de Drogas` duplicada dentro de Penal). Nosso sistema já redirecionou esses itens para as pastas titulares, mas desativar essas duplicatas evitará divisão de cadernos.
2. **Desconsiderar o "Assunto de Origem" nos cadastros antigos (`Q0001`–`Q0359`):** no banco antigo, pastas como *"Concurso de Crimes"* e *"Ação Penal (Parte 01/02)"* foram usadas como depósito genérico (em 9 questões cadastradas na origem como *Concurso de Crimes*, nenhuma tratava desse tema). Nosso sistema já reduz o peso desse metadado antigo quando o texto da questão não o confirma.
3. **Criar 3 subpastas que faltam em Legislação Especial e Processo Penal:** questões recorrentes de prova estão ficando sem subtema na árvore atual porque faltam: **(i)** *Regime aberto / Prisão domiciliar na LEP (art. 117)* dentro de `4703 Lei de Execução Penal`; **(ii)** *Procedimento Penal e Prazo de Inquérito na Lei de Drogas (arts. 48–59)* dentro de `4702 Lei de Drogas`; e **(iii)** *Procedimento dos Crimes Funcionais (arts. 513–518 do CPP)* em `Processo Penal`.
4. **Preencher uma frase de descrição nos 25 temas de Criminologia:** hoje todos os tópicos de Criminologia estão com o campo `descricao` em branco na planilha. Já adicionamos no catálogo do sistema os autores e conceitos-chave (Escola de Chicago, Anomia, Associação Diferencial, *Labelling Approach*, Vitimização primária/secundária/terciária), mas oficializar essas descrições na planilha manterá o catálogo padronizado.
