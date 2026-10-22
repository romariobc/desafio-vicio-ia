# -*- coding: utf-8 -*-
"""Pacote principal do sistema de classificação e decisão seletiva de tópicos jurídicos."""
from .modelo_sistema import ClassificadorTopicosJuridicos, intervalo_wilson
from .processamento import (
    Taxonomia,
    carregar_anexos,
    detectar_sinais_fora,
    extrair_foco_e_corpo,
    fingerprint_questao,
    limpar_html,
    normalizar,
    origem_eh_lixeira,
)

__all__ = [
    "ClassificadorTopicosJuridicos",
    "Taxonomia",
    "carregar_anexos",
    "detectar_sinais_fora",
    "extrair_foco_e_corpo",
    "fingerprint_questao",
    "intervalo_wilson",
    "limpar_html",
    "normalizar",
    "origem_eh_lixeira",
]
