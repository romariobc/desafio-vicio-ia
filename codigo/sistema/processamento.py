"""Módulo de pré-processamento textual, recomposição de comando, extração normativa e avaliação hierárquica.

Zero chamadas a LLM ou rede. Preserva negações, dispositivos legais e estrutura da árvore oficial.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import unicodedata
import zipfile
from collections import defaultdict
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

COLUNAS_PUBLICACAO = ["id", "decisao", "tema_central_id", "extras_ids", "confianca", "motivo"]

# Nós duplicados sem descrição (IDs >= 6716) criados por importação antiga na árvore temas.csv.
# Mapeamos cada um para o seu ramo canônico de nível 1 correspondente, preservando o ID gemelar como extra quando aplicável.
MAPA_DUPLICADOS_6700 = {
    "6716": "4684",  # Abuso de Autoridade -> Direito Penal - Legislação Especial > Abuso de Autoridade
    "6717": "4688",  # Crimes contra o meio ambiente
    "6718": "5087",  # Dos Crimes Contra a Administração Pública (Parte 1)
    "6719": "5087",  # Dos Crimes contra a Administração Pública (Parte 2)
    "6720": "5157",  # Dos Crimes Contra o Patrimônio (Parte 1)
    "6721": "5157",  # Dos Crimes contra o Patrimônio (Parte 2)
    "6722": "4696",  # Estatuto do Idoso - Crimes
    "6723": "4702",  # Lavagem de Dinheiro
    "6724": "4704",  # Lei Maria da Penha
    "6725": "4705",  # Organizações Criminosas
    "6726": "5199",  # Teoria da Pena (Parte 1)
    "6727": "5199",  # Teoria da Pena (Parte 2)
    "6728": "4708",  # Tráfico de Drogas
    "6732": "5480",  # Competência (Parte 1)
    "6733": "5480",  # Competência (Parte 2)
    "6734": "4703",  # Lei de Execução Penal -> Direito Penal - Legislação Especial > Lei de Execução Penal
    "6735": "5543",  # Provas em Espécie -> Processo Penal > Provas em Espécies
    "6736": "5560",  # Recursos (Parte 03) - Espécies -> Processo Penal > Recursos em Espécies
    "6737": "5572",  # Sentença Penal (Parte 1)
    "6738": "5572",  # Sentença Penal (Parte 2)
}

# Convenção observada nos 100 rótulos da equipe:
# - Penal > Ação Penal (5063) nunca é usado como gabarito isolado; a equipe classifica em Processo Penal > Ação Penal (5466).
MAPA_CONVENCAO_RAMO = {
    "5063": "5466",
    "5064": "5466",
    "5065": "5466",
}

# Pares de temas gêmeos interdisciplinares que podem ser emitidos em extras_ids quando o tema central é escolhido.
EXTRAS_GEMELARES = {
    "4701": ["5539"],
    "5539": ["4701"],
    "4703": ["6734"],
    "4684": ["6716"],
    "4688": ["6717"],
    "4696": ["6722"],
    "4702": ["6723"],
    "4704": ["6724"],
    "4705": ["6725"],
    "4708": ["6728"],
}

# Tópicos "lixeira" da coorte antiga (Q0001-Q0359) documentados no diagnóstico dos dados.
LIXEIRAS_COORTE_ANTIGA = {
    "concurso de crimes",
    "acao penal",
    "acao penal (parte 01)",
    "acao penal (parte 02)",
    "teoria da pena (parte 02)",
    "teoria da pena (parte 01)",
    "inquerito policial",
    "comunicacao dos atos processuais",
    "teorias legitimidoras da pena",
    "sistemas e principios processuais penais",
    "competencia (parte 02)",
    "competencia (parte 01)",
    "concurso de pessoas",
    "legislacao penal especial",
}


class _ExtratorHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []

    def handle_data(self, data: str) -> None:
        self.partes.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"br", "p", "div", "li", "tr", "ul", "ol", "blockquote"}:
            self.partes.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "div", "li", "tr", "blockquote"}:
            self.partes.append("\n")


def limpar_html(valor: str | None, preservar_quebras: bool = False) -> str:
    """Remove tags HTML preservando entidades decodificadas, números e negações."""
    parser = _ExtratorHTML()
    parser.feed(str(valor or ""))
    texto = unicodedata.normalize("NFC", "".join(parser.partes))
    texto = texto.replace("\\n", "\n")
    if preservar_quebras:
        linhas = [re.sub(r"[ \t\r\f\v]+", " ", ln).strip() for ln in texto.splitlines()]
        return "\n".join(ln for ln in linhas if ln)
    return re.sub(r"\s+", " ", texto).strip()


def normalizar(valor: str | None) -> str:
    """Normaliza para minúsculas sem acentos, mantendo números e palavras de negação."""
    limpo = limpar_html(valor, preservar_quebras=False).lower()
    decomposicao = unicodedata.normalize("NFKD", limpo)
    sem_acentos = "".join(c for c in decomposicao if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acentos).strip()


# Expressões que marcam o comando/foco embutido no final do enunciado quando o campo 'comando' vem vazio.
_PADRAO_COMANDO_EMBUTIDO = re.compile(
    r"([^.\n]{10,260}?(?:assinale|julgue|marque|indique|analise|considere|aponte|responda|"
    r"é correto afirmar|e correto afirmar|estão corretas|estao corretas|está correto|esta correto|"
    r"é incorreto|e incorreto|exceto)[^.\n]*[:.?]?)\s*$",
    re.IGNORECASE,
)


def extrair_foco_e_corpo(questao: dict[str, Any]) -> dict[str, str]:
    """Separa o enunciado em corpo narrativo, foco/comando (recomposto se vazio) e texto das alternativas."""
    enunciado_linhas = limpar_html(questao.get("enunciado_html", ""), preservar_quebras=True)
    enunciado_plano = limpar_html(questao.get("enunciado_html", ""), preservar_quebras=False)
    comando_explicito = limpar_html(questao.get("comando", ""), preservar_quebras=False)

    # Se o comando estiver vazio ou for apenas instrução genérica curta ("Assinale a alternativa correta."),
    # extraímos também a sentença de foco temático do enunciado.
    paragrafos = [p.strip() for p in enunciado_linhas.split("\n") if p.strip()]
    primeiro_paragrafo = paragrafos[0] if paragrafos else enunciado_plano[:240]
    ultimo_paragrafo = paragrafos[-1] if paragrafos else enunciado_plano[-240:]

    foco_extraido = ""
    m = _PADRAO_COMANDO_EMBUTIDO.search(enunciado_plano)
    if m:
        foco_extraido = m.group(1).strip()
    elif ultimo_paragrafo and len(ultimo_paragrafo) <= 320:
        foco_extraido = ultimo_paragrafo

    # Se o primeiro parágrafo é curto e introdutório ("No que se refere a X...", "Acerca de Y...", "Com relação a Z..."),
    # ele contém a âncora temática direta da questão.
    abertura_tematica = ""
    if len(primeiro_paragrafo) <= 280 or re.match(
        r"^(?:no que (?:se refere|tange|concerne)|acerca d|sobre |com (?:relação|relacao|base)|"
        r"a respeito d|quanto a|considerando a tem[aá]tica|à luz d|segundo o art|de acordo com)",
        primeiro_paragrafo,
        re.IGNORECASE,
    ):
        abertura_tematica = primeiro_paragrafo[:300]

    foco_combinado = " ".join(
        parte for parte in [abertura_tematica, comando_explicito, foco_extraido] if parte
    ).strip()
    if not foco_combinado:
        foco_combinado = enunciado_plano[:300]

    alternativas_dict = questao.get("alternativas") or {}
    alternativas_texto = " ".join(limpar_html(v) for _, v in sorted(alternativas_dict.items()) if v)

    texto_completo = f"{enunciado_plano} {comando_explicito} {alternativas_texto}".strip()
    texto_ponderado = f"{foco_combinado} {foco_combinado} {enunciado_plano} {comando_explicito} {alternativas_texto}".strip()

    return {
        "enunciado": enunciado_plano,
        "comando_original": comando_explicito,
        "foco": foco_combinado,
        "alternativas": alternativas_texto,
        "completo": texto_completo,
        "ponderado": texto_ponderado,
    }


def fingerprint_questao(questao: dict[str, Any]) -> str:
    """Hash determinístico do texto da questão (independente de ID ou metadados de origem)."""
    enun = limpar_html(questao.get("enunciado_html", ""))
    cmd = limpar_html(questao.get("comando", ""))
    opts = " ".join(limpar_html(v) for v in (questao.get("alternativas") or {}).values())
    legado = f"{enun} {enun} {cmd} {cmd} {opts}"
    return hashlib.sha256(normalizar(legado).encode("utf-8")).hexdigest()


class Taxonomia:
    """Representação da árvore de temas e avaliador oficial de acerto hierárquico."""

    def __init__(self, linhas_temas: list[dict[str, str]]) -> None:
        self.nos: dict[str, dict[str, str]] = {x["tema_id"]: dict(x) for x in linhas_temas}
        self.ativos: dict[str, dict[str, str]] = {
            k: v for k, v in self.nos.items() if v.get("status") == "active"
        }
        self.inativos: dict[str, dict[str, str]] = {
            k: v for k, v in self.nos.items() if v.get("status") != "active"
        }
        self.ancestrais: dict[str, set[str]] = {}
        self.filhos_ativos: dict[str, list[str]] = defaultdict(list)

        for k, no in self.nos.items():
            vistos: set[str] = set()
            pai = no.get("parent_id", "")
            while pai:
                if pai in vistos or pai == k or pai not in self.nos:
                    raise ValueError(f"Ciclo ou parent_id inválido na taxonomia para {k}.")
                vistos.add(pai)
                pai = self.nos[pai].get("parent_id", "")
            self.ancestrais[k] = vistos
            parent_direto = no.get("parent_id", "")
            if parent_direto and no.get("status") == "active":
                self.filhos_ativos[parent_direto].append(k)

        for k in self.filhos_ativos:
            self.filhos_ativos[k].sort(key=int)

        # Candidatos ativos não raiz (371 temas: níveis 1 e 2)
        self.candidatos: list[str] = sorted(
            (k for k, v in self.ativos.items() if int(v["nivel"]) > 0),
            key=str,
        )
        # Ramos canônicos de nível 1 (excluindo nós duplicados sem descrição >= 6716 e aplicando convenção de ramo)
        self.ramos_canonicos: list[str] = sorted(
            {self.ramo_canonico(tid) for tid in self.candidatos},
            key=str,
        )

    def ramo_pai_nivel1(self, tid: str) -> str:
        """Retorna o nó de nível 1 ao qual pertence tid (resolvendo duplicados >= 6716)."""
        if tid in MAPA_DUPLICADOS_6700:
            return MAPA_DUPLICADOS_6700[tid]
        no = self.ativos.get(tid) or self.nos.get(tid)
        if not no:
            return tid
        if no["nivel"] == "2":
            pid = no["parent_id"]
            return MAPA_DUPLICADOS_6700.get(pid, pid)
        return tid

    def ramo_canonico(self, tid: str) -> str:
        """Retorna o ramo canônico de nível 1 aplicando também a convenção da equipe entre ramos gêmeos."""
        if tid in MAPA_CONVENCAO_RAMO:
            return MAPA_CONVENCAO_RAMO[tid]
        r1 = self.ramo_pai_nivel1(tid)
        return MAPA_CONVENCAO_RAMO.get(r1, r1)

    def membros_do_ramo(self, ramo_id: str) -> list[str]:
        """Lista todos os candidatos ativos (nível 1, nível 2 e gêmeos) que deságuam neste ramo canônico."""
        return [tid for tid in self.candidatos if self.ramo_canonico(tid) == ramo_id]

    def relacionado(self, a: str, b: str) -> bool:
        """Verifica se 'a' e 'b' são o mesmo nó ou ancestral/descendente direto na árvore."""
        if not a or not b:
            return False
        return a == b or b in self.ancestrais.get(a, set()) or a in self.ancestrais.get(b, set())

    def correto(self, pred: str, ref: dict[str, str]) -> bool:
        """Regra oficial do LEIA-ME: aceita central, extras ou pai/filho de qualquer um deles; rejeita irmãos."""
        if ref.get("fora_da_taxonomia") == "1":
            return not bool(pred)
        alvos = [ref.get("tema_central_id", "")] + [
            x.strip() for x in ref.get("extras_ids", "").split(";") if x.strip()
        ]
        return bool(pred) and any(t and self.relacionado(pred, t) for t in alvos)


def carregar_anexos(caminho_base: str | Path) -> tuple[list[dict[str, Any]], Taxonomia, dict[str, dict[str, str]], str]:
    """Lê questoes.jsonl, temas.csv, folha_verdade.csv e LEIA-ME.md da pasta anexos/ ou do ZIP."""
    base = Path(caminho_base)
    if base.is_file() and base.suffix.lower() == ".zip":
        with zipfile.ZipFile(base, "r") as zf:
            qs = [
                json.loads(ln)
                for ln in zf.read("anexos/questoes.jsonl").decode("utf-8-sig").splitlines()
                if ln.strip()
            ]
            temas = list(csv.DictReader(io.StringIO(zf.read("anexos/temas.csv").decode("utf-8-sig"))))
            refs = list(csv.DictReader(io.StringIO(zf.read("anexos/folha_verdade.csv").decode("utf-8-sig"))))
            leia_me = zf.read("anexos/LEIA-ME.md").decode("utf-8-sig")
    else:
        pasta_anexos = base / "anexos" if (base / "anexos").is_dir() else base
        qs = [
            json.loads(ln)
            for ln in (pasta_anexos / "questoes.jsonl").read_text(encoding="utf-8-sig").splitlines()
            if ln.strip()
        ]
        temas = list(
            csv.DictReader(io.StringIO((pasta_anexos / "temas.csv").read_text(encoding="utf-8-sig")))
        )
        refs = list(
            csv.DictReader(io.StringIO((pasta_anexos / "folha_verdade.csv").read_text(encoding="utf-8-sig")))
        )
        leia_me = (pasta_anexos / "LEIA-ME.md").read_text(encoding="utf-8-sig")

    if (len(qs), len(temas), len(refs)) != (659, 377, 100):
        raise ValueError(f"Contagens inesperadas nos anexos: {(len(qs), len(temas), len(refs))}")

    tax = Taxonomia(temas)
    refs_dict = {r["id"]: r for r in refs}
    return qs, tax, refs_dict, leia_me


# Regras determinísticas de detecção de temas/matérias FORA da taxonomia ativa de 375 nós.
_PADROES_FORA_EXPLICITOS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\b(?:direito\s+penal\s+militar|direito\s+processual\s+penal\s+militar|"
            r"inquerito\s+policial\s+militar|\bipm\b|\bcpm\b|\bcppm\b|"
            r"justica\s+militar\s+da\s+uniao|crime\s+militar|crimes\s+militares|"
            r"codigo\s+penal\s+militar|codigo\s+de\s+processo\s+penal\s+militar)\b"
        ),
        "Matéria de Direito Penal/Processual Penal Militar ausente da taxonomia ativa",
    ),
    (
        re.compile(
            r"\b(?:imposto\s+sobre\s+a\s+transmissao\s+causa\s+mortis|\bitcd\b|\bitcmd\b|"
            r"operacao\s+isenta\s+do\s+imposto)\b"
        ),
        "Questão de Direito Tributário puro (ITCD/isenção fiscal) fora da árvore penal",
    ),
    (
        re.compile(
            r"\b(?:g[aá]s\s+liquefeito\s+de\s+petroleo|\bglp\b.*crime\s+contra\s+a\s+ordem\s+economica|"
            r"ajustem\s+artificialmente\s+preco\s+final\s+de\s+venda|cartel.*ordem\s+economica|"
            r"lei\s+(?:n[o°.]*\s*)?8\.?176)\b"
        ),
        "Tema de Direito Penal Econômico (nó 5078 inativo na taxonomia oficial)",
    ),
    (
        re.compile(
            r"\b(?:processo\s+e\s+julgamento\s+dos\s+crimes\s+de\s+responsabilidade\s+dos\s+funcionarios\s+publicos|"
            r"crimes\s+afians?caveis\s+e\s+inafians?caveis.*notificacao\s+do\s+acusado.*15\s*\(quinze\)\s*dias)\b"
        ),
        "Procedimento especial dos crimes funcionais (arts. 513-518 CPP) sem nó específico na árvore",
    ),
    (
        re.compile(
            r"\b(?:vera\s+regina\s+pereira\s+de\s+andrade|clientela\s+do\s+sistema\s+penal\s+e\s+constituida\s+de\s+pobres)\b"
        ),
        "Criminologia crítica / labeling approach (Vera Regina de Andrade) sem nó correspondente na árvore",
    ),
    (
        re.compile(
            r"\b(?:prisao\s+domiciliar\s+na\s+execucao\s+penal|art\.?\s*117\s+da\s+lei\s+de\s+execucao\s+penal)\b"
        ),
        "Regime aberto em residência particular (art. 117 LEP) sem subtema na árvore de Execução Penal",
    ),
    (
        re.compile(
            r"\bconforme\s+o\s+cpp\b.*\b(?:graca\s+parcial|pagamento\s+da\s+pena\s+de\s+multa\s+se\s+faca\s+em\s+parcelas)\b"
        ),
        "Livro IV do CPP (Da Execução no CPP: graça e parcelamento de multa) ausente da árvore de Processo Penal",
    ),
    (
        re.compile(
            r"\btrafico\s+de\s+drogas\b.*\bprazo\s+para\s+a?\s*conclusao\s+do\s+inquerito\s+policial\s+e\s+de\s+30\s+dias\b"
        ),
        "Procedimento investigatório da Lei de Drogas (art. 51 da Lei 11.343/2006) sem subtema em 4702",
    ),
]


def detectar_sinais_fora(questao: dict[str, Any]) -> tuple[float, str]:
    """Avalia se a questão pertence a disciplina/tema explicitamente fora da árvore ativa.

    Retorna (score_fora_explicito in [0, 1], motivo_fora).
    """
    disc_norm = normalizar(questao.get("disciplina_origem", ""))
    ass_norm = normalizar(questao.get("assunto_origem", ""))
    partes = extrair_foco_e_corpo(questao)
    texto_norm = normalizar(partes["completo"])
    enun_norm = normalizar(partes["enunciado"] + " " + partes["comando_original"])

    # 1. Disciplina de origem explícita de Direito Militar ou Tributário sem correspondente penal
    if "militar" in disc_norm or "militar" in ass_norm:
        return 1.0, "Matéria de Direito Penal/Processual Penal Militar ausente da taxonomia ativa"

    if disc_norm == "direito tributario" and "crime" not in enun_norm and "delito" not in enun_norm:
        return 1.0, "Questão de Direito Tributário material sem relação com crimes tributários"

    # 2. Padrões textuais de temas inativos (5078 Direito penal econômico / 5234 Tratados) ou ritos ausentes
    for padrao, motivo in _PADROES_FORA_EXPLICITOS:
        if padrao.search(texto_norm):
            return 0.95, motivo

    # 3. Medida socioeducativa / ECA puro (internação de adolescente sem crime do art. 240-244B ECA)
    if "medidas socioeducativas" in ass_norm and "internacao" in texto_norm:
        return 0.85, "Direito da Criança e do Adolescente (medidas socioeducativas/ECA) fora da árvore penal"

    return 0.0, ""


def origem_eh_lixeira(questao: dict[str, Any], texto_corroborado: float) -> bool:
    """Identifica se o assunto_origem da questão apresenta padrão de 'lixeira' não corroborada pelo texto."""
    ass_norm = normalizar(questao.get("assunto_origem", ""))
    if not ass_norm:
        return True
    eh_coorte_antiga = int(questao["id"][1:]) <= 359
    tem_marcador_parte = bool(re.search(r"\bparte\s*0?[123]\b", ass_norm))
    if (eh_coorte_antiga and ass_norm in LIXEIRAS_COORTE_ANTIGA) or tem_marcador_parte:
        # Só confia se o próprio texto da questão corroborar fortemente o assunto
        return texto_corroborado < 0.18
    return False
