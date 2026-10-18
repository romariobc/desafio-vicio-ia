# Desafio de classificação de questões jurídicas

[![Reproduzir o experimento](https://github.com/romariobc/desafio-vicio-ia/actions/workflows/reproducao.yml/badge.svg)](https://github.com/romariobc/desafio-vicio-ia/actions/workflows/reproducao.yml)

Organizei a entrega em três artefatos na raiz e uma pasta com o sistema reproduzível:

| Entrega | Conteúdo |
|---|---|
| `publicacao.csv` | Registro das 359 decisões, com tema, extras, confiança e motivo |
| `previsao.txt` | Minha previsão original de precisão e cobertura, com explicação e limites |
| `RELATORIO.md` e `RELATORIO.docx` | Meu relatório, em versão de leitura e editável, com memo ao professor |
| [`codigo/`](codigo/README.md) | Código, entradas necessárias, prompts, revisão humana, testes e instruções de reprodução e escala |

Deleguei a execução técnica ao agente GPT no Codex Desktop. No sistema, preservo os checkpoints da interpretação feita pelo agente e reconstruo tratamento, calibração, decisões e métricas. Não executo uma nova inferência nessa reprodução.

## Como reproduzo

Uso Python 3.10 ou superior, apenas com biblioteca padrão. Depois de clonar ou baixar e extrair o repositório, executo na raiz:

```powershell
python codigo/reproduzir.py
```

Também posso entrar em `codigo/` e executar `python reproduzir.py`. Recebo as saídas reconstruídas em `codigo/saidas/`; preservo os arquivos de entrega na raiz.

Explico [como usei o código, como reproduzo e como ampliaria a operação](codigo/README.md) no README da pasta `codigo/`.
