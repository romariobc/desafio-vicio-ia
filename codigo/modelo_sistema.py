# -*- coding: utf-8 -*-
"""
Motor Híbrido de Ranqueamento Multi-Canal, Roll-up Hierárquico para Ramo Canônico (Nível 1),
Calibração de Confiança Out-of-Fold e Política de Decisão Seletiva (Publicar / Revisar / Fora).

Restrição de Tempo de Decisão (conforme PDF do Case):
- ZERO chamadas a LLMs ou encoders em tempo de execução.
- Consome exclusivamente os textos dos anexos e os artefatos pré-computados em `artefatos/`.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from processamento import (
    EXTRAS_GEMELARES,
    Taxonomia,
    carregar_anexos,
    detectar_sinais_fora,
    extrair_foco_e_corpo,
    fingerprint_questao,
    limpar_html,
    normalizar,
    origem_eh_lixeira,
)
from preparar_artefatos import ENRIQUECIMENTO_COMPLEMENTAR

STOP_WORDS_PT = (
    "a o as os de da do das dos em no na nos nas e ou que se um uma para por com "
    "ao aos pelo pela sobre quanto qual quais segundo assinale alternativa correta "
    "incorreta direito disciplina tema subtema questoes source path"
).split()

TERMOS_LEI_ESPECIAL = [
    " 9.099 ", " 9099 ", " juizado especial ", " jecrim ", " menor potencial ofensivo ",
    " transacao penal ", " suspensao condicional do processo ", " 7.210 ", " 7210 ",
    " execucao penal ", " durante a execucao da pena ", " progressao de regime ",
    " progressao do regime prisional ", " periodo minimo para a progressao ",
    " remicao ", " falta grave ", " saida temporaria ",
    " 11.340 ", " 11340 ", " maria da penha ", " 11.343 ", " 11343 ", " trafico de drogas ",
    " 8.072 ", " 8072 ", " crimes hediondos ", " 12.850 ", " 12850 ", " organizacao criminosa ",
    " colaboracao premiada ", " 10.741 ", " 10741 ", " estatuto do idoso ",
    " 9.613 ", " 9613 ", " lavagem de dinheiro ", " 10.826 ", " 10826 ", " desarmamento ",
    " 9.455 ", " 9455 ", " 13.869 ", " 13869 ", " 13.260 ", " 13260 ", " terrorismo ",
]

NOMES_FEATURES_CALIBRACAO = [
    "sc1",
    "sc2",
    "margin12",
    "margin13",
    "ratio12",
    "entropia5",
    "ancora_b1",
    "sup_b1",
    "max_sim_viz",
    "lex_raw_b1",
    "foc_raw_b1",
    "sem_raw_b1",
    "lex_top1_agree",
    "lex_top2_agree",
    "sem_top1_agree",
    "sem_top2_agree",
    "meta_agree",
    "eh_lixeira",
    "lixeira_sem_suporte",
    "score_fora",
]


def _minmax_linhas(m: np.ndarray) -> np.ndarray:
    lo = m.min(axis=1, keepdims=True)
    hi = m.max(axis=1, keepdims=True)
    return (m - lo) / np.maximum(hi - lo, 1e-6)


def intervalo_wilson(acertos: int, total: int, z: float = 1.96) -> Tuple[float, float]:
    """Calcula o intervalo de confiança de Wilson para proporção binomial."""
    if total <= 0:
        return 0.0, 1.0
    p = acertos / total
    denom = 1.0 + (z * z) / total
    centro = (p + (z * z) / (2.0 * total)) / denom
    margem = (z / denom) * math.sqrt((p * (1.0 - p)) / total + (z * z) / (4.0 * total * total))
    return max(0.0, centro - margem), min(1.0, centro + margem)


class ClassificadorTopicosJuridicos:
    """
    Sistema completo da Abordagem 1:
    1. Extração estrutural de foco decisório e detecção de questões fora do escopo (`fora`).
    2. Ranqueamento híbrido sobre os 371 nós ativos (Léxico próprio/família/foco, Semântico cacheado
       original/enriquecido, Âncoras normativas/doutrinárias curadas, Metadado com gate anti-lixeira
       e Suporte de vizinhos rotulados com exclusão estrita de self/duplicatas).
    3. Roll-up Hierárquico para Ramo Canônico de Nível 1 (elimina erros de irmão de subtema mantendo
       100% de aceitação pela regra oficial de ramo).
    4. Calibração de probabilidade Out-of-Fold e Política de Decisão com meta >= 95% de precisão.
    """

    def __init__(self, pasta_etapa2: Path):
        self.pasta_etapa2 = Path(pasta_etapa2)
        self.pasta_anexos = self.pasta_etapa2 / "anexos"
        self.pasta_artefatos = self.pasta_etapa2 / "artefatos"

        self.questoes, self.tax, self.referencias, self.leia_me = carregar_anexos(
            self.pasta_anexos
        )
        self.catalogo = json.loads(
            (self.pasta_artefatos / "catalogo_temas.json").read_text(encoding="utf-8")
        )
        cache_npz = np.load(
            self.pasta_artefatos / "embeddings_cache.npz", allow_pickle=False
        )

        self.q_ids: List[str] = [str(x) for x in cache_npz["q_ids"]]
        self.t_ids: List[str] = [str(x) for x in cache_npz["t_ids"]]
        self.q_idx_map: Dict[str, int] = {qid: i for i, qid in enumerate(self.q_ids)}
        self.t_idx_map: Dict[str, int] = {tid: j for j, tid in enumerate(self.t_ids)}

        self.vecs_q = cache_npz["questoes"].astype(np.float32)
        self.vecs_t_orig = cache_npz["temas_orig"].astype(np.float32)
        self.vecs_t_perf = cache_npz["temas_perf"].astype(np.float32)

        # Pré-processamento estrutural de todas as 659 questões
        self.partes_qs = [extrair_foco_e_corpo(q) for q in self.questoes]
        self.fingerprints = [fingerprint_questao(q) for q in self.questoes]
        self.sinais_fora = [detectar_sinais_fora(q) for q in self.questoes]

        self._construir_matrizes_base()

    def _construir_matrizes_base(self) -> None:
        textos_ponderados = [p["ponderado"] for p in self.partes_qs]
        textos_foco = [p["enunciado"] + " " + p["foco"] for p in self.partes_qs]
        assuntos_orig = [limpar_html(q.get("assunto_origem", "")) for q in self.questoes]

        docs_proprio = [self.catalogo["nos"][tid]["texto_proprio"] for tid in self.t_ids]
        docs_familia = [self.catalogo["nos"][tid]["texto_familia"] for tid in self.t_ids]
        titulos_temas = [self.catalogo["nos"][tid]["titulo"] for tid in self.t_ids]

        word_vec = TfidfVectorizer(
            strip_accents="unicode",
            lowercase=True,
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words=STOP_WORDS_PT,
            max_features=60000,
        )
        char_vec = TfidfVectorizer(
            strip_accents="unicode",
            lowercase=True,
            analyzer="char_wb",
            ngram_range=(3, 5),
            sublinear_tf=True,
            max_features=60000,
        )

        corpus_fit = docs_proprio + docs_familia + textos_ponderados
        word_vec.fit(corpus_fit)
        char_vec.fit(corpus_fit)

        self.qw_pond = word_vec.transform(textos_ponderados)
        self.qc_pond = char_vec.transform(textos_ponderados)
        qw_foco = word_vec.transform(textos_foco)
        qc_foco = char_vec.transform(textos_foco)
        sw_orig = word_vec.transform(assuntos_orig)
        sc_orig = char_vec.transform(assuntos_orig)

        tw_prop = word_vec.transform(docs_proprio)
        tc_prop = char_vec.transform(docs_proprio)
        tw_fam = word_vec.transform(docs_familia)
        tc_fam = char_vec.transform(docs_familia)
        mw_tit = word_vec.transform(titulos_temas)
        mc_tit = char_vec.transform(titulos_temas)

        self.sim_lex_prop = (
            0.65 * (self.qw_pond @ tw_prop.T).toarray()
            + 0.35 * (self.qc_pond @ tc_prop.T).toarray()
        ).astype(np.float32)
        self.sim_lex_fam = (
            0.65 * (self.qw_pond @ tw_fam.T).toarray()
            + 0.35 * (self.qc_pond @ tc_fam.T).toarray()
        ).astype(np.float32)
        self.sim_foco_prop = (
            0.70 * (qw_foco @ tw_prop.T).toarray()
            + 0.30 * (qc_foco @ tc_prop.T).toarray()
        ).astype(np.float32)
        self.sim_meta = (
            0.65 * (sw_orig @ mw_tit.T).toarray()
            + 0.35 * (sc_orig @ mc_tit.T).toarray()
        ).astype(np.float32)

        self.sim_sem_orig = (self.vecs_q @ self.vecs_t_orig.T).astype(np.float32)
        self.sim_sem_perf = (self.vecs_q @ self.vecs_t_perf.T).astype(np.float32)

        # Normalização por linha [0, 1]
        self.s_lex_p = _minmax_linhas(self.sim_lex_prop)
        self.s_lex_f = _minmax_linhas(self.sim_lex_fam)
        self.s_foc_p = _minmax_linhas(self.sim_foco_prop)
        self.s_sem_o = _minmax_linhas(self.sim_sem_orig)
        self.s_sem_p = _minmax_linhas(self.sim_sem_perf)
        self.s_meta = _minmax_linhas(self.sim_meta)

        # Canal de Âncoras Normativas/Doutrinárias Curadas
        self.hit_ancora = np.zeros((len(self.questoes), len(self.t_ids)), dtype=np.float32)
        norm_foco_qs = [" " + normalizar(t) + " " for t in textos_foco]
        norm_full_qs = [" " + normalizar(p["completo"]) + " " for p in self.partes_qs]

        for j, tid in enumerate(self.t_ids):
            comp = ENRIQUECIMENTO_COMPLEMENTAR.get(tid, {})
            termos = [normalizar(t) for t in comp.get("termos", []) if len(t) >= 4]
            if not termos:
                continue
            for i in range(len(self.questoes)):
                c_foco = sum(1 for t in termos if f" {t} " in norm_foco_qs[i])
                c_full = sum(1 for t in termos if f" {t} " in norm_full_qs[i])
                if c_foco or c_full:
                    self.hit_ancora[i, j] = min(1.0, 0.45 * c_foco + 0.20 * c_full)

        # Matriz de compatibilidade disciplinar
        self.disc_compat = np.ones((len(self.questoes), len(self.t_ids)), dtype=np.float32)
        for i, q in enumerate(self.questoes):
            d_orig = normalizar(q.get("disciplina_origem", ""))
            ass_orig = normalizar(q.get("assunto_origem", ""))
            tem_lei_esp = (
                any(x in norm_full_qs[i] for x in TERMOS_LEI_ESPECIAL)
                or "legislacao penal especial" in ass_orig
            )
            for j, tid in enumerate(self.t_ids):
                d_tema = self.tax.ativos[tid]["disciplina"]
                if d_orig in {"penal", "direito penal"}:
                    if d_tema == "Penal":
                        self.disc_compat[i, j] = 1.0
                    elif d_tema == "Direito Penal - Legislação Especial":
                        self.disc_compat[i, j] = (
                            1.0 if (tem_lei_esp or self.hit_ancora[i, j] > 0) else 0.55
                        )
                    else:
                        self.disc_compat[i, j] = 0.0
                elif d_orig in {"processo penal", "direito processual penal"}:
                    if d_tema == "Processo Penal":
                        self.disc_compat[i, j] = 1.0
                    elif d_tema == "Direito Penal - Legislação Especial":
                        self.disc_compat[i, j] = (
                            1.0 if (tem_lei_esp or self.hit_ancora[i, j] > 0) else 0.55
                        )
                    else:
                        self.disc_compat[i, j] = 0.0
                elif d_orig == "criminologia":
                    self.disc_compat[i, j] = 1.0 if d_tema == "Criminologia" else 0.0
                elif d_orig == "direito penal - legislacao especial":
                    self.disc_compat[i, j] = (
                        1.0 if d_tema == "Direito Penal - Legislação Especial" else 0.70
                    )

        # Gate anti-lixeira para o assunto_origem
        self.meta_gate = np.ones(len(self.questoes), dtype=np.float32)
        self.eh_lixeira_flag = np.zeros(len(self.questoes), dtype=bool)
        for i, q in enumerate(self.questoes):
            best_m = int(np.argmax(self.sim_meta[i]))
            corrob = float(max(self.sim_lex_prop[i, best_m], self.sim_foco_prop[i, best_m]))
            if origem_eh_lixeira(q, corrob):
                self.meta_gate[i] = 0.12
                self.eh_lixeira_flag[i] = True

        # Matriz de similaridade par-a-par entre todas as 659 questões (para kNN ágil)
        sim_q_sem = self.vecs_q @ self.vecs_q.T
        sim_q_lex = (
            0.65 * (self.qw_pond @ self.qw_pond.T).toarray()
            + 0.35 * (self.qc_pond @ self.qc_pond.T).toarray()
        ).astype(np.float32)
        self.sim_q_hibrida = (0.65 * sim_q_sem + 0.35 * sim_q_lex).astype(np.float32)

        # Mapa de nó -> ramo canônico
        self.ramo_de_no = [self.tax.ramo_canonico(tid) for tid in self.t_ids]
        self.ramos_unicos = sorted(set(self.ramo_de_no), key=lambda x: int(x))
        self.ramo_para_indices: Dict[str, List[int]] = {
            r: [j for j, rb in enumerate(self.ramo_de_no) if rb == r]
            for r in self.ramos_unicos
        }

    def construir_banco_rotulos(self, ids_treino: List[str]) -> Tuple[List[int], np.ndarray]:
        """Constrói matriz (N_treino x 371) de alvos hierárquicos para suporte kNN."""
        tr_idx = [self.q_idx_map[qid] for qid in ids_treino]
        label_mat = np.zeros((len(tr_idx), len(self.t_ids)), dtype=np.float32)
        for r_i, q_i in enumerate(tr_idx):
            qid = self.questoes[q_i]["id"]
            ref = self.referencias[qid]
            alvos = [ref["tema_central_id"]] + [
                x for x in ref["extras_ids"].split(";") if x
            ]
            for j, tid in enumerate(self.t_ids):
                label_mat[r_i, j] = max(
                    (
                        1.0
                        if tid == t
                        else 0.70
                        if self.tax.relacionado(tid, t)
                        else 0.0
                        for t in alvos
                        if t
                    ),
                    default=0.0,
                )
        return tr_idx, label_mat

    def ranquear_questao(
        self, i: int, tr_idx: List[int], label_mat: np.ndarray
    ) -> Dict:
        """
        Calcula os scores de todos os 371 nós e dos 88 ramos canônicos para a questão `i`,
        garantindo exclusão estrita da própria questão e de duplicatas de texto no banco kNN.
        """
        fp_i = self.fingerprints[i]
        mask_validos = [
            k_i
            for k_i, q_tr in enumerate(tr_idx)
            if q_tr != i and self.fingerprints[q_tr] != fp_i
        ]
        if mask_validos:
            idx_banco = [tr_idx[k_i] for k_i in mask_validos]
            near = self.sim_q_hibrida[i, idx_banco]
            top_k_local = np.argsort(-near)[:3]
            pesos_viz = near[top_k_local]
            mat_viz = label_mat[[mask_validos[k] for k in top_k_local]]
            sup = (pesos_viz @ mat_viz) / 3.0
            max_sim_viz = float(pesos_viz[0]) if len(pesos_viz) > 0 else 0.0
        else:
            sup = np.zeros(len(self.t_ids), dtype=np.float32)
            max_sim_viz = 0.0

        s_sup = sup / max(float(sup.max()), 1e-6)

        node_score = (
            0.24 * self.s_lex_p[i]
            + 0.14 * self.s_lex_f[i]
            + 0.18 * self.s_foc_p[i]
            + 0.15 * self.s_sem_o[i]
            + 0.15 * self.s_sem_p[i]
            + 0.22 * self.hit_ancora[i]
            + 0.14 * s_sup
            + 0.10 * float(self.meta_gate[i]) * self.s_meta[i]
        ) * (0.15 + 0.85 * self.disc_compat[i])

        # Score de cada ramo canônico = máximo entre os nós daquele ramo
        branch_scores: List[Tuple[str, float, str]] = []
        for r in self.ramos_unicos:
            idxs = self.ramo_para_indices[r]
            best_local = idxs[int(np.argmax(node_score[idxs]))]
            branch_scores.append((r, float(node_score[best_local]), self.t_ids[best_local]))

        branch_scores.sort(key=lambda x: x[1], reverse=True)
        b1, sc1, no1 = branch_scores[0]
        gemeos_b1 = set(EXTRAS_GEMELARES.get(b1, []))
        concorrentes = [x for x in branch_scores[1:] if x[0] not in gemeos_b1]
        b2, sc2, no2 = concorrentes[0]
        b3, sc3, no3 = concorrentes[1]

        # Concordância entre canais independentes (no nível de ramo canônico)
        lex_comb = (
            0.50 * self.s_lex_p[i] + 0.30 * self.s_foc_p[i] + 0.20 * self.s_lex_f[i]
        ) * self.disc_compat[i]
        sem_comb = (0.50 * self.s_sem_o[i] + 0.50 * self.s_sem_p[i]) * self.disc_compat[i]
        meta_comb = self.s_meta[i] * self.disc_compat[i]

        lex_top_branches = []
        for idx in np.argsort(-lex_comb)[:5]:
            rb = self.ramo_de_no[int(idx)]
            if rb not in lex_top_branches:
                lex_top_branches.append(rb)

        sem_top_branches = []
        for idx in np.argsort(-sem_comb)[:5]:
            rb = self.ramo_de_no[int(idx)]
            if rb not in sem_top_branches:
                sem_top_branches.append(rb)

        meta_best_branch = self.ramo_de_no[int(np.argmax(meta_comb))]
        meta_best_raw = float(np.max(self.sim_meta[i] * (self.disc_compat[i] > 0)))

        idxs_b1 = self.ramo_para_indices[b1]
        ancora_b1 = float(np.max(self.hit_ancora[i, idxs_b1]))
        sup_b1 = float(np.max(sup[idxs_b1]))
        lex_raw_b1 = float(np.max(self.sim_lex_prop[i, idxs_b1]))
        foc_raw_b1 = float(np.max(self.sim_foco_prop[i, idxs_b1]))
        sem_raw_b1 = float(np.max(self.sim_sem_perf[i, idxs_b1]))

        # Entropia dos top-5 ramos
        top5_vals = np.array([x[1] for x in branch_scores[:5]], dtype=np.float64)
        exp_v = np.exp((top5_vals - top5_vals.max()) * 8.0)
        probs_5 = exp_v / exp_v.sum()
        entropia_5 = float(-np.sum(probs_5 * np.log(np.maximum(probs_5, 1e-12))) / math.log(5.0))

        # Sinais de fora da taxonomia
        score_fora_exp, motivo_fora_exp = self.sinais_fora[i]
        score_fora = float(score_fora_exp)

        max_aderencia_bruta = max(lex_raw_b1, foc_raw_b1, ancora_b1)
        if sem_raw_b1 < 0.34 and max_aderencia_bruta < 0.10:
            score_fora = max(score_fora, 0.72)
            if not motivo_fora_exp:
                motivo_fora_exp = (
                    "Baixa aderência lexical e semântica a todos os ramos ativos da taxonomia"
                )

        # Seleção de extras_ids (temas secundários de alta confiança ou par gemelar 4701<->5539)
        extras: List[str] = []
        if b1 in EXTRAS_GEMELARES:
            for gem in EXTRAS_GEMELARES[b1]:
                if gem not in extras and gem != b1 and gem in self.tax.ativos:
                    extras.append(gem)
        if sc2 >= 0.86 * sc1 and sc2 >= 0.58 and b2 != b1 and b2 not in extras:
            extras.append(b2)

        eh_lix = 1.0 if self.eh_lixeira_flag[i] else 0.0
        lix_sem_sup = 1.0 if (eh_lix > 0.5 and sup_b1 < 0.05 and ancora_b1 <= 0.20) else 0.0

        familia_b1 = {b1} | gemeos_b1
        features = {
            "sc1": sc1,
            "sc2": sc2,
            "margin12": sc1 - sc2,
            "margin13": sc1 - sc3,
            "ratio12": sc1 / max(sc2, 1e-4),
            "entropia5": entropia_5,
            "ancora_b1": ancora_b1,
            "sup_b1": sup_b1,
            "max_sim_viz": max_sim_viz,
            "lex_raw_b1": lex_raw_b1,
            "foc_raw_b1": foc_raw_b1,
            "sem_raw_b1": sem_raw_b1,
            "lex_top1_agree": 1.0 if (lex_top_branches and lex_top_branches[0] in familia_b1) else 0.0,
            "lex_top2_agree": 1.0 if any(rb in familia_b1 for rb in lex_top_branches[:2]) else 0.0,
            "sem_top1_agree": 1.0 if (sem_top_branches and sem_top_branches[0] in familia_b1) else 0.0,
            "sem_top2_agree": 1.0 if any(rb in familia_b1 for rb in sem_top_branches[:2]) else 0.0,
            "meta_agree": 1.0
            if (not self.eh_lixeira_flag[i] and meta_best_raw >= 0.35 and meta_best_branch in familia_b1)
            else 0.0,
            "eh_lixeira": eh_lix,
            "lixeira_sem_suporte": lix_sem_sup,
            "score_fora": score_fora,
        }

        return {
            "qid": self.questoes[i]["id"],
            "ramo_top1": b1,
            "no_especifico_top1": no1,
            "ramo_top2": b2,
            "no_especifico_top2": no2,
            "extras_ids": extras[:2],
            "features": features,
            "motivo_fora_detector": motivo_fora_exp,
        }

    @staticmethod
    def _vetor_features(f: Dict[str, float]) -> np.ndarray:
        return np.array([f[k] for k in NOMES_FEATURES_CALIBRACAO], dtype=np.float64)

    @staticmethod
    def _confianca_analitica(f: Dict[str, float]) -> float:
        p_ana = (
            0.28 * min(1.0, f["sc1"] / 0.85)
            + 0.22 * min(1.0, f["margin12"] / 0.18)
            + 0.14 * (1.0 - f["entropia5"])
            + 0.12 * min(1.0, f["ancora_b1"] + 0.5 * f["sup_b1"])
            + 0.12 * (0.5 * f["lex_top1_agree"] + 0.5 * f["sem_top1_agree"])
            + 0.07 * (0.5 * f["lex_top2_agree"] + 0.5 * f["sem_top2_agree"])
            + 0.05 * f["meta_agree"]
            - 0.08 * f["eh_lixeira"]
            - 0.12 * f["lixeira_sem_suporte"]
            - 0.65 * f["score_fora"]
        )
        return float(max(0.01, min(0.99, p_ana)))

    def treinar_calibrador(self, ids_treino: List[str]) -> Tuple[Pipeline, List[int], np.ndarray]:
        tr_idx, label_mat = self.construir_banco_rotulos(ids_treino)
        X_tr, y_tr = [], []
        for qid in ids_treino:
            i = self.q_idx_map[qid]
            r = self.ranquear_questao(i, tr_idx, label_mat)
            X_tr.append(self._vetor_features(r["features"]))
            y_tr.append(
                1 if self.tax.correto(r["ramo_top1"], self.referencias[qid]) else 0
            )
        modelo_cal = make_pipeline(
            StandardScaler(),
            LogisticRegression(C=0.25, class_weight="balanced", random_state=42),
        )
        modelo_cal.fit(np.array(X_tr), np.array(y_tr))
        return modelo_cal, tr_idx, label_mat

    def estimar_confianca(self, r: Dict, modelo_cal: Pipeline) -> float:
        f = r["features"]
        x = self._vetor_features(f).reshape(1, -1)
        p_lr = float(modelo_cal.predict_proba(x)[0, 1])
        p_ana = self._confianca_analitica(f)
        conf = 0.45 * p_lr + 0.55 * p_ana
        return float(max(0.01, min(0.99, conf)))

    def construir_motivo_revisao(self, r: Dict) -> str:
        b1 = r["ramo_top1"]
        b2 = r["ramo_top2"]
        t1 = self.tax.ativos[b1]["titulo"]
        t2 = self.tax.ativos[b2]["titulo"]
        f = r["features"]
        if f["margin12"] < 0.12:
            return f"margem estreita entre {b1} ({t1}) e {b2} ({t2})"
        if f["lex_top1_agree"] < 0.5 and f["sem_top1_agree"] < 0.5:
            return f"divergencia entre canais lexico e semantico; sugestao {b1} ({t1}) vs {b2} ({t2})"
        if f["eh_lixeira"] > 0.5:
            return f"assunto de origem inconsistente; duvida entre {b1} ({t1}) e {b2} ({t2})"
        return f"confianca intermediaria; duvida entre {b1} ({t1}) e {b2} ({t2})"

    def decidir_questao(
        self,
        r: Dict,
        conf: float,
        limiar_publicar: float = 0.575,
        limiar_fora: float = 0.70,
    ) -> Dict[str, str]:
        f = r["features"]
        if f["score_fora"] >= limiar_fora:
            motivo = (
                r["motivo_fora_detector"]
                or "Tema ou disciplina ausente da taxonomia ativa de Direito Penal/Processual/Criminologia"
            )
            return {
                "id": r["qid"],
                "decisao": "fora",
                "tema_central_id": "",
                "extras_ids": "",
                "confianca": f"{min(conf, 0.15):.2f}",
                "motivo": motivo,
            }

        if conf >= limiar_publicar:
            return {
                "id": r["qid"],
                "decisao": "publicar",
                "tema_central_id": r["ramo_top1"],
                "extras_ids": ";".join(r["extras_ids"]),
                "confianca": f"{conf:.2f}",
                "motivo": "",
            }

        return {
            "id": r["qid"],
            "decisao": "revisar",
            "tema_central_id": r["ramo_top1"],
            "extras_ids": ";".join(r["extras_ids"]),
            "confianca": f"{conf:.2f}",
            "motivo": self.construir_motivo_revisao(r),
        }

    def avaliar_validacao_cruzada(
        self,
        divisoes_path: Optional[Path] = None,
        limiar_publicar: float = 0.575,
        limiar_fora: float = 0.70,
    ) -> Dict:
        """
        Executa validação cruzada de 5 dobras (folds externos estritos) sobre as 100 questões
        da folha_verdade.csv para auditar acurácia top-1, calibração e precisão seletiva.
        """
        if divisoes_path is None:
            cand_local = self.pasta_artefatos / "divisoes_validacao.json"
            if cand_local.exists():
                divisoes_path = cand_local
            else:
                divisoes_path = (
                    self.pasta_etapa2.parent.parent
                    / "etapa2"
                    / "experimentos"
                    / "ancoras-capacidade-v1"
                    / "divisoes.json"
                )
        divisoes = json.loads(Path(divisoes_path).read_text(encoding="utf-8"))

        oof_registros = {}
        relatorio_dobras = []

        for idx_rod, rod in enumerate(divisoes["rodadas"]):
            tr_ids = rod["desenvolvimento"] + rod["calibracao"]
            ext_ids = rod["externa"]
            modelo_cal, tr_idx, label_mat = self.treinar_calibrador(tr_ids)

            hits_dobra = 0
            pub_dobra = 0
            pub_hits_dobra = 0

            for qid in ext_ids:
                i = self.q_idx_map[qid]
                r = self.ranquear_questao(i, tr_idx, label_mat)
                conf = self.estimar_confianca(r, modelo_cal)
                dec = self.decidir_questao(r, conf, limiar_publicar, limiar_fora)
                ref = self.referencias[qid]
                acerto_top1 = self.tax.correto(r["ramo_top1"], ref)
                fora_real = ref["fora_da_taxonomia"] == "1"

                hits_dobra += int(acerto_top1)
                if dec["decisao"] == "publicar":
                    pub_dobra += 1
                    pub_hits_dobra += int(acerto_top1)

                oof_registros[qid] = {
                    "qid": qid,
                    "decisao": dec["decisao"],
                    "tema_central_id": dec["tema_central_id"],
                    "ramo_top1": r["ramo_top1"],
                    "confianca": conf,
                    "acerto_top1": bool(acerto_top1),
                    "fora_real": bool(fora_real),
                    "score_fora": r["features"]["score_fora"],
                }

            relatorio_dobras.append(
                {
                    "id_rodada": rod.get("id", rod.get("rodada", idx_rod + 1)),
                    "n_externa": len(ext_ids),
                    "acertos_top1": hits_dobra,
                    "acuracia_top1": hits_dobra / len(ext_ids),
                    "publicadas": pub_dobra,
                    "acertos_publicadas": pub_hits_dobra,
                    "precisao_publicar": (pub_hits_dobra / pub_dobra) if pub_dobra else 1.0,
                }
            )

        todos = list(oof_registros.values())
        em_tax = [x for x in todos if not x["fora_real"]]
        fora_tax = [x for x in todos if x["fora_real"]]
        publicadas = [x for x in todos if x["decisao"] == "publicar"]
        revisar = [x for x in todos if x["decisao"] == "revisar"]
        fora_dec = [x for x in todos if x["decisao"] == "fora"]

        n_pub = len(publicadas)
        n_pub_hits = sum(1 for x in publicadas if x["acerto_top1"])
        prec_pub = n_pub_hits / n_pub if n_pub else 1.0
        ic95_prec = intervalo_wilson(n_pub_hits, n_pub, z=1.96)
        ic90_prec = intervalo_wilson(n_pub_hits, n_pub, z=1.645)

        curva_limiares = []
        for th in np.round(np.linspace(0.50, 0.80, 13), 3):
            pub_th = [
                x
                for x in todos
                if x["confianca"] >= th and x["score_fora"] < limiar_fora
            ]
            if not pub_th:
                continue
            h_th = sum(1 for x in pub_th if x["acerto_top1"])
            curva_limiares.append(
                {
                    "limiar": float(th),
                    "publicadas": len(pub_th),
                    "cobertura": len(pub_th) / len(todos),
                    "acertos": h_th,
                    "precisao": h_th / len(pub_th),
                }
            )

        # Brier score sobre acertos top-1
        confs_arr = np.array([x["confianca"] for x in todos], dtype=np.float64)
        hits_arr = np.array([1.0 if x["acerto_top1"] else 0.0 for x in todos], dtype=np.float64)
        brier = float(np.mean((confs_arr - hits_arr) ** 2))

        return {
            "n_referencias": len(todos),
            "n_em_taxonomia": len(em_tax),
            "n_fora_taxonomia": len(fora_tax),
            "acertos_top1_total": sum(1 for x in todos if x["acerto_top1"]),
            "acuracia_top1_total": sum(1 for x in todos if x["acerto_top1"]) / len(todos),
            "acuracia_top1_em_taxonomia": sum(1 for x in em_tax if x["acerto_top1"]) / len(em_tax),
            "limiar_publicar": limiar_publicar,
            "limiar_fora": limiar_fora,
            "publicadas_oof": n_pub,
            "cobertura_publicar_oof": n_pub / len(todos),
            "acertos_publicadas_oof": n_pub_hits,
            "precisao_publicar_oof": prec_pub,
            "precisao_ic95_wilson": [round(ic95_prec[0], 4), round(ic95_prec[1], 4)],
            "precisao_ic90_wilson": [round(ic90_prec[0], 4), round(ic90_prec[1], 4)],
            "revisar_oof": len(revisar),
            "fora_oof": len(fora_dec),
            "fora_reais_capturadas_nao_publicadas": sum(
                1 for x in fora_tax if x["decisao"] != "publicar"
            ),
            "brier_score_oof": round(brier, 4),
            "dobras": relatorio_dobras,
            "curva_limiares": curva_limiares,
        }

    def executar_inferencia_completa(
        self,
        limiar_publicar: float = 0.575,
        limiar_fora: float = 0.70,
    ) -> Tuple[List[Dict[str, str]], Dict]:
        """
        Treina o calibrador final nas 100 questões de referência (com features Leave-One-Out
        isentas de auto-vazamento) e classifica as 659 questões de `questoes.jsonl`.
        """
        ids_ref = sorted(self.referencias.keys())
        modelo_cal, tr_idx, label_mat = self.treinar_calibrador(ids_ref)

        linhas_publicacao: List[Dict[str, str]] = []
        estatisticas_559 = {
            "total_avaliadas_fora_folha": 0,
            "publicar": 0,
            "revisar": 0,
            "fora": 0,
            "soma_confianca_publicadas": 0.0,
            "por_coorte": {
                "antiga_Q0001_Q0359": {"total": 0, "publicar": 0, "revisar": 0, "fora": 0},
                "nova_Q0360_Q0659": {"total": 0, "publicar": 0, "revisar": 0, "fora": 0},
            },
        }

        for i, q in enumerate(self.questoes):
            qid = q["id"]
            r = self.ranquear_questao(i, tr_idx, label_mat)
            conf = self.estimar_confianca(r, modelo_cal)
            dec = self.decidir_questao(r, conf, limiar_publicar, limiar_fora)
            linhas_publicacao.append(dec)

            if qid not in self.referencias:
                estatisticas_559["total_avaliadas_fora_folha"] += 1
                d_str = dec["decisao"]
                estatisticas_559[d_str] += 1
                if d_str == "publicar":
                    estatisticas_559["soma_confianca_publicadas"] += conf
                coorte_k = (
                    "antiga_Q0001_Q0359" if int(qid[1:]) <= 359 else "nova_Q0360_Q0659"
                )
                estatisticas_559["por_coorte"][coorte_k]["total"] += 1
                estatisticas_559["por_coorte"][coorte_k][d_str] += 1

        n_pub_559 = estatisticas_559["publicar"]
        n_tot_559 = estatisticas_559["total_avaliadas_fora_folha"]
        estatisticas_559["cobertura_publicar_559"] = (
            n_pub_559 / n_tot_559 if n_tot_559 else 0.0
        )
        estatisticas_559["confianca_media_publicadas_559"] = (
            estatisticas_559["soma_confianca_publicadas"] / n_pub_559 if n_pub_559 else 0.0
        )
        return linhas_publicacao, estatisticas_559
