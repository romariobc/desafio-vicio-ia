# Sistema reproduzível do desafio

Reuni nesta pasta somente a implementação, as entradas, os instrumentos de revisão e as evidências necessárias para reproduzir e compreender o experimento. Posso copiar `codigo/` para outra pasta e executá-la isoladamente: não dependo dos relatórios ou CSVs que ficam na raiz do repositório.

## Como usei o código

Orientei o agente GPT a ler as fontes e a árvore, tratar as 359 questões, registrar as classificações com evidência, comparar com referência humana, calibrar a confiança e aplicar uma política congelada. Deleguei a execução técnica ao agente; o avaliador humano forneceu os pareceres.

Preservei a interpretação semântica em `dados/decisoes/`. O código reconstrói o processamento desses checkpoints, não uma nova inferência GPT. Registrei a configuração como GPT-6.1 Sol com esforço de raciocínio médio no Codex Desktop. Não medi tokens, custo marginal ou duração integral dessa interpretação.

## Como reproduzo

Uso **Python 3.10+**, sem bibliotecas externas ou chave de API. Depois de clonar ou extrair o ZIP, entro nesta pasta:

```powershell
cd codigo
python reproduzir.py
```

Na raiz do repositório, uso a alternativa `python codigo/reproduzir.py`. No Windows, posso usar `py -3` no lugar de `python`; em Linux/macOS, `python3`. Não uso `-O`, pois as regras dependem de assertions.

Para escolher outra pasta de saída, executo:

```powershell
python reproduzir.py --saida ../minha-reproducao
```

Não preciso baixar novamente os anexos, instalar pacotes nem acessar outra pasta do projeto. Depois do download, executo sem conexão. A integração contínua verifica a reprodução em Windows e Linux.

## O que executo

| Etapa | Implementação | Resultado |
|---|---|---|
| Verificar entradas e montar área limpa | `sistema/executar.py` e `mapa_reproducao.json` | Confiro hashes e extraio os anexos do ZIP original |
| Tratar dados | `sistema/preparar.py` | Reconstruo textos, árvore ativa e lotes de leitura |
| Preparar referência | `sistema/referencia.py` | Reconstruo a revisão inicial normalizada e a partição 42/18 |
| Calibrar e decidir | `sistema/pipeline.py` | Reaplico os checkpoints, ajustes e regras; gero CSV e previsão original |
| Gerar visão navegável | `sistema/relatorio.py` | Reconstruo a árvore HTML e uma visão técnica temporária |
| Verificar regras e organização | `testes/` | Executo 13 testes das regras e três de organização |
| Avaliar experimentos | `sistema/avaliacao/` | Refaço o sorteio, a comparação cega e a adjudicação |
| Apresentar a previsão | `sistema/previsao.py` | Melhoro a explicação mantendo as quatro linhas numéricas originais |

Monto temporariamente o layout usado pelos scripts originais para preservar seus contratos. Não uso dados tratados ou métricas prontas como entradas. Copio fontes, decisões GPT, revisões humanas e contratos congelados; reconstruo as demais informações. O gerador técnico temporário não substitui o relatório da entrega.

## Onde encontro os arquivos

```text
codigo/
  reproduzir.py      ponto de entrada
  sistema/           implementação, prompts e mapa de montagem
  dados/             fontes originais e decisões GPT congeladas
  interfaces/        microsites usados na revisão humana
  experimentos/      pareceres recebidos, plano e comparações
  auditoria/         hashes, configuração, política e validação
  testes/            testes automatizados
  docs/              explicações detalhadas e evolução proposta
```

Depois de executar, encontro em `saidas/`:

- `publicacao.csv` e `previsao.txt`: entrega reconstruída, conferida com os hashes esperados;
- `previsao_original.txt`: versão anterior à revisão editorial, também conferida;
- `validacao_final.json` e `execucao.log`: contagens, verificações e registro da execução;
- `arvore.html`, `dados_tratados/` e `lotes_leitura/`: visualização e preparação reconstruídas;
- `referencias/`, `metricas/` e `avaliacoes/`: referência normalizada, calibração e experimentos recalculados.

Não versiono `saidas/`. Espero `hashes_identicos: true`, 359 questões, 316 publicar, 39 revisar e quatro fora; 13 testes das regras e três de organização aprovados. Reproduzo 14/26 na comparação cega e 25/26 na adjudicada. O tempo do comando mede apenas o processamento local.

## Como organizei a avaliação humana

Usei `interfaces/avaliacao_cega.html` sem sugestões visíveis e `interfaces/conferencia_divergencias.html` para conferir os desacordos. Para abrir as telas, baixo a pasta e uso um navegador; não dependo de servidor. Preciso exportar JSON e CSV para transferir e validar os pareceres.

Preservei os registros de um experimento encerrado. Para outra revisão, eu criaria uma cópia versionada, registraria autoria e exposição anterior e validaria conclusão, IDs e temas ativos. Não substituiria as exportações congeladas.

Obtive cobertura de 316/359 = 88,02%. Preservei a previsão de 95,37%. A concordância foi 53,85% na revisão cega e 96,15% após conferência com sugestões visíveis. Mudou a referência humana, não o modelo; não considero comprovada a meta mínima oficial de 95% nem uma redução causal de ancoragem.

## Como ampliaria a escala

Para novos lotes e 50 mil questões semanais, eu construiria uma etapa de inferência automatizada, começando com poucos itens e medindo qualidade, tempo e custo antes de ampliar. Eu preservaria versões de texto, taxonomia, prompt, modelo, referência e calibrador. Usaria fila, processamento incremental por ID/hash, concorrência limitada, retentativas e checkpoints.

Usaria embeddings para recuperar candidatos somente após medir se o tema correto aparece entre eles; uma LLM interpretaria a questão e produziria resposta estruturada. Compararia um classificador treinado após reunir referência suficiente. Reservaria agentes para orquestração quando necessários; não tomaria concordância entre agentes como validação independente.

Começaria com Python, armazenamento versionado e banco relacional. Consideraria Databricks se já estivesse na empresa ou se múltiplas importações justificassem governança adicional. Não considero essas ferramentas obrigatórias, nem as executei neste case.

Planejaria amostras semanais de publicadas para revisão sem sugestões, além da fila de dúvidas e exclusões. Integraria reportes de alunos como incidentes, com julgamento humano, correção rastreável e testes de regressão. Separaria desenvolvimento, calibração e teste, reduzindo a automação se a qualidade não atendesse ao limite aprovado.

O código atual reproduz o case de 359 questões; não transportaria seu calibrador como garantia para outra população. Detalho as escolhas, a capacidade humana e os cenários de custo em [Escala e manutenção](docs/ESCALA_E_MANUTENCAO.md).

## Como verifico e mantenho

Confiro entradas e saídas por `auditoria/manifesto_reproducao.json`. Preservo a previsão original em `auditoria/previsao_original.txt` e explico a revisão editorial em `auditoria/revisao_previsao.json`. Não alterei as quatro linhas numéricas após os experimentos.

Se encontrar hash diferente, uso uma cópia limpa ou crio uma nova versão do experimento. Não modifico os registros para fazer a checagem passar. Ao abrir CSV no Excel, trabalho em uma cópia para evitar alteração de separadores ou codificação. Se a execução falhar, verifico a mensagem e não considero saídas parciais como resultado aprovado.

Mantenho os detalhes em [Fluxo executado](docs/FLUXO_EXECUTADO.md), [Revisão humana](docs/REVISAO_HUMANA.md) e [Resultados](experimentos/RESULTADOS.md). Os registros anteriores continuam recuperáveis no histórico Git.
