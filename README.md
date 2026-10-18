# Classificação de questões jurídicas com IA

[![Reproduzir o experimento](https://github.com/romariobc/desafio-vicio-ia/actions/workflows/reproducao.yml/badge.svg)](https://github.com/romariobc/desafio-vicio-ia/actions/workflows/reproducao.yml)

Este é o sistema de reprodução do desafio: **fontes + decisões GPT registradas + referência humana → tratamento, calibração, regras e avaliação → arquivos da entrega**.

O ponto de entrada é `reproduzir.py`; a implementação está em `sistema/`. Ele reconstrói o experimento de 359 questões sem chave de API, instalação de pacotes ou acesso a outra pasta local. A interpretação semântica foi realizada pelo agente no Codex Desktop e está preservada em checkpoints: a reprodução não executa uma nova inferência.

## A entrega está na raiz

| Arquivo | Para que serve |
|---|---|
| `publicacao.csv` | Decisão, tema, extras, confiança e motivo para cada uma das 359 questões |
| `previsao.txt` | Previsão original de precisão e cobertura, com intervalos e explicação |
| `RELATORIO.md` | Relatório da solução, versão textual da V3 revisada |
| `RELATORIO.docx` | Mesmo relatório em formato editável; cinco páginas, com memo ao professor na última |

## Executar

Requer **Python 3.10+**, apenas com biblioteca padrão. Git serve somente para clonar; também é possível baixar em **Code → Download ZIP** e extrair.

```powershell
git clone https://github.com/romariobc/desafio-vicio-ia.git
cd desafio-vicio-ia
python reproduzir.py
```

Se baixou o ZIP, abra o terminal na pasta extraída e execute a última linha. No Windows, `py -3 reproduzir.py` é uma alternativa; em Linux/macOS, use `python3 reproduzir.py` quando necessário. Não use `-O`, pois as validações usam assertions.

O comando verifica hashes, monta uma área temporária limpa, extrai os anexos originais, trata os dados, reaplica os checkpoints GPT, reconstrói a referência, calibra, gera as decisões, executa os testes e recalcula os experimentos. Os arquivos entregues na raiz são preservados. Os resultados reconstruídos aparecem em **`saidas/`**, fora do versionamento.

```text
saidas/
  publicacao.csv / previsao.txt   arquivos reconstruídos e comparados à entrega
  validacao_final.json            hashes, contagens, testes e tempo local
  execucao.log                   registro dos passos executados
  arvore.html                    árvore navegável das classificações
  dados_tratados/                 questões limpas, temas e diagnóstico
  lotes_leitura/                  lotes reconstruídos
  referencias/                   referência normalizada e partições de calibração/avaliação
  metricas/                      rodadas, calibrador e política
  avaliacoes/                    sorteio, comparação cega e adjudicação
```

Para usar outra pasta: `python reproduzir.py --saida ../minha-reproducao`.

**Execução aprovada:** `hashes_identicos: true`, 359 questões, 316 publicar, 39 revisar e quatro fora; 13 testes das regras e três de organização aprovados. A comparação cega reproduz 14/26 e a adjudicada, 25/26. O tempo medido é apenas o processamento local, sem a inferência GPT ou o trabalho humano.

## Onde está cada parte

```text
sistema/        código do pipeline, avaliação, prompts e mapa de reprodução
testes/         testes das regras e da organização
dados/          fontes originais e classificações GPT congeladas
interfaces/     os dois microsites usados pelo avaliador humano
experimentos/   revisões recebidas, plano e resultados da avaliação
auditoria/      hashes, política congelada, configuração e verificações
docs/           detalhes do fluxo, da revisão e da evolução para produção
```

- [Fluxo executado e funcionamento dos scripts](docs/FLUXO_EXECUTADO.md)
- [Uso das interfaces de revisão humana](docs/REVISAO_HUMANA.md)
- [Escala, automação, ferramentas e manutenção](docs/ESCALA_E_MANUTENCAO.md)
- [Resultados e limites dos experimentos](experimentos/RESULTADOS.md)

Abra `interfaces/avaliacao_cega.html` para o instrumento sem sugestões e `interfaces/conferencia_divergencias.html` para a conferência guiada. São páginas locais, com salvamento e exportação de respostas; representam o experimento encerrado. Para nova revisão, use uma cópia versionada e preserve as evidências recebidas.

## Como interpretar o resultado

A cobertura é **316/359 = 88,02%**; a previsão congelada de precisão é **95,37%**. Na amostra, a concordância nas publicadas foi **14/26 = 53,85%** na revisão cega e **25/26 = 96,15%** após adjudicação com sugestões visíveis.

Na conferência mudaram os rótulos humanos, sem mudança nas classificações ou probabilidades do modelo. Não se comprovou precisão mínima de 95% no gabarito reservado da empresa, nem redução causal de ancoragem. A amostra é pequena, parte dos itens tinha exposição anterior e os intervalos são descritivos. O relatório e `experimentos/` preservam os resultados favoráveis e desfavoráveis.

## Verificação e manutenção

`auditoria/manifesto_reproducao.json` registra as entradas e as saídas esperadas. `sistema/mapa_reproducao.json` torna explícito como os arquivos são montados temporariamente para executar os scripts originais. O ZIP é a fonte única dos anexos; saídas tratadas, lotes e visualizações são gerados pelo comando, sem cópias prontas usadas como entrada.

Se um hash divergir, use uma cópia limpa ou abra uma nova versão do experimento; não altere os registros para fazer a verificação passar. Preserve CSVs originais ao abrir no Excel, que pode alterar codificação e separadores. Os arquivos anteriores à reorganização permanecem recuperáveis no histórico Git.

O pipeline atual reproduz este case. O serviço de inferência para novos lotes e 50 mil questões semanais, a auditoria contínua e as ferramentas opcionais estão descritos separadamente no documento de escala.
