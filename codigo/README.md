# Arquitetura do Sistema (`codigo/`)

Esta pasta concentra todo o código-fonte, os dados de entrada, os artefatos pré-computados e a suíte de testes automatizados, organizados por responsabilidade para facilitar leitura, manutenção e auditoria.

---

## 1. Organização de Pastas e Responsabilidades

```text
codigo/
├── README.md                      # Documentação técnica da arquitetura interna
├── requirements.txt               # Dependências científicas de execução (numpy, scipy, scikit-learn)
├── reproduzir.py                  # Ponto de entrada único: regenera publicacao.csv e previsao.txt na raiz
├── dados/                         # Fontes oficiais imutáveis do desafio
│   ├── anexos/                    # questoes.jsonl (659), temas.csv (377), folha_verdade.csv (100), LEIA-ME.md
│   ├── anexos-case-ia.zip         # Pacote zip original dos anexos
│   └── case-ia-classificacao-de-topicos.pdf
├── artefatos/                     # Artefatos estáticos versionados (100% autocontidos)
│   ├── insumos_base_temas.json    # Perfis conceituais legislativos e dicionário de normas/siglas
│   ├── catalogo_temas.json        # Catálogo enriquecido dos 371 nós candidatos e 88 ramos canônicos
│   ├── embeddings_cache.npz       # Vetores densos 384d (paraphrase-multilingual-MiniLM-L12-v2)
│   ├── divisoes_validacao.json    # Partições estratificadas das 5 dobras de validação cruzada
│   ├── manifesto_artefatos.json   # Hashes SHA-256 de integridade e linhagem dos artefatos
│   └── metricas_validacao.json    # Saída auditável de métricas OOF, ablação de coorte e projeção de escala
├── sistema/                       # Núcleo de domínio e motor de classificação (Zero LLM em decisão)
│   ├── __init__.py                # Exportação pública das classes e funções do domínio
│   ├── processamento.py           # Limpeza HTML preservando negações, extração de foco, Taxonomia e detectores
│   ├── modelo_sistema.py          # Ranqueador híbrido 8 canais, Roll-up Nível 1, calibração OOF e decisão
│   └── preparar_artefatos.py      # Script autocontido para reconstrução de catalogo_temas.json e cache .npz
└── testes/                        # Auditoria automatizada e testes de regressão
    └── test_sistema.py            # 8 testes cobrindo contrato CSV, AST zero-LLM, Roll-up e sincronia documental
```

---

## 2. Fluxo de Dados entre os Módulos (`sistema/`)

1. **[`sistema/processamento.py`](sistema/processamento.py)** — *Camada de Domínio e Pré-processamento:*
   - `limpar_html` e `extrair_foco_e_corpo`: higieniza o HTML preservando operadores de negação (`não`, `exceto`, `incorreta`, `salvo`) e isola a pergunta decisória (`comando` explícito ou período final do `enunciado_html` nas 300 questões da coorte nova) juntamente com as alternativas.
   - `Taxonomia`: modela os 377 nós de `temas.csv`, filtra os 2 nós inativos (`5078`, `5234`) e os 4 nós de nível 0, implementa a regra oficial de acerto (`correto`) e o mapeamento para os 88 ramos canônicos de nível 1 (`ramo_canonico`).
   - `detectar_sinais_fora` e `origem_eh_lixeira`: identifica matérias fora da árvore ativa (Direito Militar, Tributário puro, ordem econômica inativa, dispositivos sem subtema) e sinaliza tópicos "lixeira" da coorte antiga.

2. **[`sistema/preparar_artefatos.py`](sistema/preparar_artefatos.py)** — *Camada de Preparação Offline Autocontida:*
   - Combina `artefatos/insumos_base_temas.json` com o dicionário curado `ENRIQUECIMENTO_COMPLEMENTAR` (cobrindo os 25 nós de Criminologia que vieram sem descrição em `temas.csv` e os principais institutos de Penal e Processo Penal) para gerar `artefatos/catalogo_temas.json` e validar `artefatos/embeddings_cache.npz`.

3. **[`sistema/modelo_sistema.py`](sistema/modelo_sistema.py)** — *Camada de Ranqueamento, Calibração e Decisão:*
   - `ClassificadorTopicosJuridicos`: combina 8 canais de evidência (TF-IDF próprio, família e foco; embeddings MiniLM originais e enriquecidos; âncoras normativas curadas; suporte kNN em matriz $O(N \cdot M_{\text{ref}})$ de dimensão `659 x 100` com exclusão de duplicatas por hash SHA-1; e metadado com gate anti-lixeira), aplica o Roll-up para Ramo Canônico de Nível 1 e executa a decisão seletiva exigindo `confianca >= 0.575` e corroboração mínima de pelo menos 2 famílias de canais (`tem_convergencia_minima`).

---

## 3. Comandos de Execução

A partir da raiz do repositório:

```bash
# Regenerar publicacao.csv, previsao.txt e codigo/artefatos/metricas_validacao.json
python -X utf8 codigo/reproduzir.py

# Executar os 8 testes unitários e contratuais
python -X utf8 codigo/testes/test_sistema.py

# Reconstruir o catálogo de temas e validar o manifesto de artefatos
python -X utf8 codigo/sistema/preparar_artefatos.py
```
