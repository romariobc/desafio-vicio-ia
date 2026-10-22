# Case IA — Classificação de Tópicos Jurídicos (Etapa 2)

[![Reproduzir o experimento](https://github.com/romariobc/desafio-vicio-ia/actions/workflows/reproducao.yml/badge.svg)](https://github.com/romariobc/desafio-vicio-ia/actions/workflows/reproducao.yml)

Sistema determinístico de classificação hierárquica, calibração de confiança e decisão seletiva (`publicar`, `revisar`, `fora`) para questões de concursos públicos nas disciplinas de **Direito Penal**, **Direito Processual Penal**, **Direito Penal - Legislação Especial** e **Criminologia**.

---

## 1. Arquivos de Entrega na Raiz

Mantemos na raiz do repositório exclusivamente os artefatos de entrega exigidos pelo desafio e a pasta [`codigo/`](codigo/README.md):

| Entrega | Descrição |
|---|---|
| [`publicacao.csv`](publicacao.csv) | Classificação final das **659 questões** (`id,decisao,tema_central_id,extras_ids,confianca,motivo`) |
| [`previsao.txt`](previsao.txt) | Autoavaliação quantitativa (`precisao_prevista`, `precisao_intervalo`, `cobertura_prevista`, `cobertura_intervalo`) e justificativa |
| [`RELATORIO.md`](RELATORIO.md) | Relatório técnico estruturado nas seções **(a)** Diagnóstico, **(b)** Desenho, **(c)** Validação/Calibração, **(d)** Escala/Operação e **(e)** Limitações |
| [`MEMO_PROFESSOR.md`](MEMO_PROFESSOR.md) | Memorando executivo de 1 página destinado à coordenação pedagógica / professor da área |
| [`codigo/`](codigo/README.md) | Sistema completo em arquitetura limpa (`reproduzir.py`, `sistema/`, `dados/`, `artefatos/`, `testes/`) |

---

## 2. Como Reproduzir (Zero Chamadas a LLM em Tempo de Decisão)

Em conformidade com a **Seção 4 do PDF do Case**, o fluxo de decisão não realiza chamadas a modelos de linguagem (LLMs), APIs externas ou encoders neurais: consome apenas os anexos oficiais (`codigo/dados/anexos/`) e os artefatos pré-computados (`codigo/artefatos/`).

```bash
# 1. Instalar dependências científicas locais (numpy, scipy, scikit-learn)
pip install -r codigo/requirements.txt

# 2. Regenerar publicacao.csv, previsao.txt e codigo/artefatos/metricas_validacao.json
python -X utf8 codigo/reproduzir.py

# 3. Executar a suíte de testes unitários e auditoria contratual (8 testes)
python -X utf8 codigo/testes/test_sistema.py
```

A documentação detalhada dos módulos internos encontra-se em [`codigo/README.md`](codigo/README.md).

---

## 3. Resumo dos Resultados Verificados

| Indicador | Resultado Verificado |
|---|---|
| **Acurácia Top-1 em Taxonomia (5 dobras externas — 92 refs)** | **89,13%** (`82/92`) — evolução de +27,1 p.p. sobre a baseline plana (`62,0%`) |
| **Acurácia Top-1 Global (5 dobras externas — 100 refs)** | **82,00%** (`82/100`) |
| **Precisão Observada em `decisao = publicar` (OOF nas 5 dobras)** | **96,77%** (`60/62`, IC 95% de Wilson: `88,98%–99,11%`, Brier Score: `0,1249`) |
| **Precisão Prevista (`previsao.txt`, com desconto prudencial de 1,5 p.p.)** | **95,00%** (`0.95`, intervalo `0.89-0.99`) |
| **Ablação Estrutural Formato Coorte Nova (100 refs sem `comando` separado)** | **82/100** Top-1 e **96,83%** (`61/63`) de precisão OOF (vetores MiniLM fixos) |
| **Cobertura Realizada de `publicar` nas 559 questões fora da folha** | **54,03%** (`302/559`) — `42,1%` (`109/259`) na coorte antiga e **`64,3%`** (`193/300`) na coorte nova |
| **Encaminhadas para `revisar` (fora da `folha_verdade.csv`)** | **43,11%** (`241/559`) — todas com `tema_central_id` sugerido e `motivo` diagnóstico |
| **Identificadas como `fora` da taxonomia (fora da `folha_verdade.csv`)** | **2,86%** (`16/559`) — Direito Militar, Tributário puro, ordem econômica inativa (`5078`), etc. |
