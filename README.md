# Case IA — Classificação de Tópicos Jurídicos (Etapa 2)

[![Reproduzir o experimento](https://github.com/romariobc/desafio-vicio-ia/actions/workflows/reproducao.yml/badge.svg)](https://github.com/romariobc/desafio-vicio-ia/actions/workflows/reproducao.yml)

Sistema determinístico de classificação hierárquica, calibração de confiança e decisão seletiva (`publicar`, `revisar`, `fora`) para questões de concursos públicos nas disciplinas de **Direito Penal**, **Direito Processual Penal**, **Direito Penal - Legislação Especial** e **Criminologia**.

---

## 1. Estrutura da Entrega

```text
.
├── publicacao.csv                 # Entrega principal: 659 questões classificadas (id,decisao,tema_central_id,extras_ids,confianca,motivo)
├── previsao.txt                   # Autoavaliação quantitativa (precisão e cobertura previstas fora da folha_verdade + fundamentação)
├── RELATORIO.md                   # Relatório técnico (seções a, b, c, d, e do edital do case)
├── MEMO_PROFESSOR.md              # Memorando executivo de 1 página para a coordenação pedagógica / professor da área
├── README.md                      # Instruções de reprodução e documentação da arquitetura
├── requirements.txt               # Dependências científicas locais (numpy, scipy, scikit-learn)
├── anexos/                        # Dados oficiais de entrada (questoes.jsonl, temas.csv, folha_verdade.csv, entrega_modelo.csv, LEIA-ME.md)
├── artefatos/                     # Artefatos pré-computados e versionados (100% autocontidos no repositório)
│   ├── insumos_base_temas.json    # Perfis legislativos e dicionário de normas/siglas versionados no repositório
│   ├── catalogo_temas.json        # Catálogo enriquecido de 371 nós ativos e 88 ramos canônicos
│   ├── embeddings_cache.npz       # Vetores densos 384d (paraphrase-multilingual-MiniLM-L12-v2) pré-computados
│   ├── divisoes_validacao.json    # Divisões estratificadas das 5 dobras de validação cruzada
│   ├── manifesto_artefatos.json   # Hashes SHA-256 de auditoria e linhagem dos artefatos
│   └── metricas_validacao.json    # Métricas OOF, ablação estrutural da coorte nova e benchmark de escala 50k
└── codigo/                        # Código-fonte modular em Python 3.10+
    ├── processamento.py           # Limpeza HTML preservando negações, extração de foco decisório, taxonomia e detectores de fora/lixeira
    ├── preparar_artefatos.py      # Geração autocontida dos artefatos a partir de anexos/ e artefatos/insumos_base_temas.json
    ├── modelo_sistema.py          # Ranqueador híbrido multi-canal, Roll-up para Ramo Canônico, calibração e política seletiva
    ├── reproduzir.py              # Script principal de reprodução em tempo de decisão (ZERO chamadas a LLM/encoders)
    └── test_sistema.py            # Suíte de testes unitários e auditoria contratual (AST, esquema, taxonomia, memória e consistência)
```

---

## 2. Como Reproduzir as Entregas (Zero Chamadas a LLM)

Em conformidade estrita com a **Seção 4 do PDF do Case**, o comando de reprodução (`codigo/reproduzir.py`) **não realiza chamadas a modelos de linguagem (LLMs), APIs externas ou encoders neurais em tempo de decisão**. Ele consome apenas os arquivos de `anexos/` e os artefatos estáticos versionados em `artefatos/`.

### Pré-requisitos
- Python `>= 3.10` (validado em Python `3.12`)
- Instalação das dependências científicas locais:

```bash
pip install -r requirements.txt
```

### Comando Único de Regeneração (`publicacao.csv` + `previsao.txt` + `artefatos/metricas_validacao.json`)

A partir da raiz do repositório:

```bash
python -X utf8 codigo/reproduzir.py
```

Tempo médio de execução: **~14 segundos** em CPU local (sendo `~2,6 segundos` para a inferência das 659 questões).

### Execução da Suíte de Testes e Auditoria

```bash
python -X utf8 codigo/test_sistema.py
```

### Regeneração Autocontida dos Artefatos de Catálogo

O script de preparação é **100% autocontido no repositório** (lê apenas `anexos/` e `artefatos/insumos_base_temas.json`, sem depender de caminhos externos):

```bash
python -X utf8 codigo/preparar_artefatos.py
```

*(Opcional: caso deseje recalcular os vetores densos 384d do zero a partir dos textos usando `fastembed`, execute `pip install fastembed` e rode `python -X utf8 codigo/preparar_artefatos.py --recalcular-embeddings`.)*

---

## 3. Resumo dos Resultados Verificados (`artefatos/metricas_validacao.json`)

| Métrica | Resultado Verificado |
|---|---|
| **Acurácia Top-1 em Taxonomia (5 dobras externas — 92 refs)** | **89,13%** (`82/92`) — evolução de +27,1 p.p. sobre a baseline plana (`62,0%`) |
| **Acurácia Top-1 Global (5 dobras externas — 100 refs)** | **82,00%** (`82/100`) |
| **Precisão Observada em `decisao = publicar` (OOF nas 5 dobras)** | **96,77%** (`60/62`, IC 95% de Wilson: `88,98%–99,11%`, Brier Score: `0,1249`) |
| **Precisão Prevista (`previsao.txt`, com desconto de seleção pós-hoc)** | **95,00%** (`0.95`, intervalo previsto: `0.89-0.99`) |
| **Ablação Estrutural Formato Coorte Nova (100 refs sem `comando` separado)** | **82/100** Top-1 e **96,83%** (`61/63`) de precisão OOF (vetores MiniLM fixos) |
| **Cobertura Realizada de `publicar` nas 559 questões fora da folha** | **54,03%** (`302/559`) — `42,1%` (`109/259`) na coorte antiga e **`64,3%`** (`193/300`) na coorte nova |
| **Encaminhadas para `revisar` (fora da `folha_verdade.csv`)** | **43,11%** (`241/559`) — todas com `tema_central_id` sugerido e `motivo` diagnóstico |
| **Identificadas como `fora` da taxonomia (fora da `folha_verdade.csv`)** | **2,86%** (`16/559`) — Direito Militar, Tributário puro, ordem econômica inativa (`5078`), etc. |
