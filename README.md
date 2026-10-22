# Case IA — Classificação de Tópicos Jurídicos (Etapa 2)

[![Reproduzir o experimento](https://github.com/romariobc/desafio-vicio-ia/actions/workflows/reproducao.yml/badge.svg)](https://github.com/romariobc/desafio-vicio-ia/actions/workflows/reproducao.yml)

Sistema determinístico de classificação hierárquica, calibração de confiança Out-of-Fold e decisão seletiva (`publicar`, `revisar`, `fora`) para questões de concursos públicos nas disciplinas de **Direito Penal**, **Direito Processual Penal**, **Direito Penal - Legislação Especial** e **Criminologia**.

---

## 1. Estrutura da Entrega

```text
etapa 2/
├── publicacao.csv                 # Entrega principal: 659 questões classificadas (id,decisao,tema_central_id,extras_ids,confianca,motivo)
├── previsao.txt                   # Autoavaliação quantitativa (precisão e cobertura previstas fora da folha_verdade + justificativa)
├── RELATORIO.md                   # Relatório técnico (seções a, b, c, d, e do edital do case)
├── MEMO_PROFESSOR.md              # Memorando executivo de 1 página para a coordenação pedagógica / professor da área
├── README.md                      # Instruções de reprodução e documentação da arquitetura
├── anexos/                        # Dados oficiais de entrada (questoes.jsonl, temas.csv, folha_verdade.csv, entrega_modelo.csv, LEIA-ME.md)
├── artefatos/                     # Artefatos pré-computados e versionados (consumidos sem chamadas de LLM/rede)
│   ├── catalogo_temas.json        # Catálogo enriquecido de 371 nós ativos e 88 ramos canônicos
│   ├── embeddings_cache.npz       # Vetores densos 384d (paraphrase-multilingual-MiniLM-L12-v2) pré-computados
│   ├── divisoes_validacao.json    # Divisões estratificadas das 5 dobras de validação cruzada
│   ├── manifesto_artefatos.json   # Hashes SHA-256 de auditoria e linhagem dos artefatos
│   └── metricas_validacao.json    # Relatório completo das métricas Out-of-Fold e distribuição das 659 questões
└── codigo/                        # Código-fonte modular em Python 3.12
    ├── processamento.py           # Limpeza HTML preservando negações, extração de foco decisório, taxonomia e detectores de fora/lixeira
    ├── preparar_artefatos.py      # Geração e empacotamento dos artefatos estáticos e perfis normativos/doutrinários
    ├── modelo_sistema.py          # Ranqueador híbrido multi-canal, Roll-up para Ramo Canônico, calibração OOF e política de decisão
    ├── reproduzir.py              # Script principal de reprodução em tempo de decisão (ZERO chamadas a LLM/encoders)
    └── test_sistema.py            # Suíte de testes unitários e auditoria contratual (AST, esquema, taxonomia e métricas)
```

---

## 2. Como Reproduzir as Entregas (Zero Chamadas a LLM)

Em conformidade estrita com a **Seção 4 do PDF do Case**, o comando de reprodução (`codigo/reproduzir.py`) **não realiza chamadas a modelos de linguagem (LLMs), APIs externas ou encoders neurais em tempo de decisão**. Ele consome apenas os arquivos de `anexos/` e os artefatos estáticos versionados em `artefatos/`.

### Pré-requisitos
- Python `>= 3.10` (validado em Python `3.12.14`)
- Bibliotecas científicas padrão: `numpy`, `scipy`, `scikit-learn`

### Comando Único de Regeneração (`publicacao.csv` + `previsao.txt`)

No PowerShell (a partir da raiz ou usando o ambiente virtual configurado):

```powershell
& "E:\Labdev\Projetos\desafio-vicio\etapa2\.venv\Scripts\python.exe" -X utf8 "E:\Labdev\Projetos\desafio-vicio\PIPILINE\etapa 2\codigo\reproduzir.py"
```

Tempo médio de execução: **~12 segundos** em CPU local.

### Execução da Suíte de Testes e Auditoria

```powershell
& "E:\Labdev\Projetos\desafio-vicio\etapa2\.venv\Scripts\python.exe" -X utf8 "E:\Labdev\Projetos\desafio-vicio\PIPILINE\etapa 2\codigo\test_sistema.py"
```

*(Opcional)* Para regerar os artefatos estáticos (`artefatos/catalogo_temas.json` e `artefatos/embeddings_cache.npz`) antes da inferência:

```powershell
& "E:\Labdev\Projetos\desafio-vicio\etapa2\.venv\Scripts\python.exe" -X utf8 "E:\Labdev\Projetos\desafio-vicio\PIPILINE\etapa 2\codigo\preparar_artefatos.py"
```

---

## 3. Resumo dos Resultados Obtidos

| Métrica | Resultado Validado |
|---|---|
| **Acurácia Top-1 (5 folds externos — 92 questões em taxonomia)** | **89,13%** (`82/92`) — evolução de +27,1 p.p. sobre a baseline plana (`62,0%`) |
| **Acurácia Top-1 Global (5 folds externos — todas as 100 referências)** | **82,00%** (`82/100`) |
| **Precisão em `decisao = publicar` (Out-of-Fold nas 5 dobras)** | **96,77%** (`60/62`, sendo **100%** nas questões dentro da taxonomia ativa) |
| **Cobertura de `publicar` nas 559 questões fora da `folha_verdade.csv`** | **57,07%** (`319/559`) — `44,8%` na coorte antiga e **`67,3%`** na coorte nova |
| **Encaminhadas para `revisar` (fora da `folha_verdade.csv`)** | **40,07%** (`224/559`) — todas com `tema_central_id` sugerido e `motivo` explícito |
| **Identificadas como `fora` da taxonomia (fora da `folha_verdade.csv`)** | **2,86%** (`16/559`) — Direito Militar, Tributário puro, ordem econômica inativa (`5078`), etc. |
