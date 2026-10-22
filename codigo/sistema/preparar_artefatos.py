"""Script de preparação offline dos artefatos estáticos versionados da Etapa 2.

Gera em `etapa 2/artefatos/`:
1. `catalogo_temas.json`: Catálogo enriquecido dos 375 temas ativos (definições legislativas,
   termos canônicos, dispositivos normativos e agregação familiar de subtemas nos ramos de nível 1).
2. `embeddings_cache.npz`: Vetores densos de 384 dimensões (paraphrase-multilingual-MiniLM-L12-v2)
   para as 659 questões e os 371 temas candidatos (originais e enriquecidos).
3. `manifesto_artefatos.json`: Hashes SHA-256 e proveniência auditável.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

PASTA_SISTEMA = Path(__file__).resolve().parent
PASTA_CODIGO = PASTA_SISTEMA.parent
PASTA_ETAPA2 = PASTA_CODIGO.parent
PASTA_DADOS = PASTA_CODIGO / "dados"
PASTA_ARTEFATOS = PASTA_CODIGO / "artefatos"
if str(PASTA_SISTEMA) not in sys.path:
    sys.path.insert(0, str(PASTA_SISTEMA))

from processamento import MAPA_CONVENCAO_RAMO, MAPA_DUPLICADOS_6700, carregar_anexos, normalizar

# Enriquecimento doutrinário e normativo estático para os nós (especialmente Criminologia e Teoria do Crime/Processo)
# que estavam sem enriquecimento legislativo direto, baseado na estrutura da taxonomia e na legislação penal/processual.
ENRIQUECIMENTO_COMPLEMENTAR: dict[str, dict[str, list[str] | str]] = {
    # Criminologia
    "4366": {
        "definicao": "Tipologias e classificações vitimológicas segundo a participação ou culpabilidade da vítima no delito.",
        "termos": [
            "mendelsohn", "von hentig", "vitima completamente inocente", "vitima ideal",
            "vitima menos culpada", "vitima por ignorancia", "vitima tao culpada quanto o infrator",
            "vitima provocadora", "vitima mais culpada", "vitima unicamente culpada",
            "vitima agressora", "vitima simuladora", "vitima imaginaria", "dupla penal",
        ],
    },
    "4367": {
        "definicao": "Sistemas de classificação de criminosos e delinquentes nas escolas antropológica, clínica e sociológica.",
        "termos": [
            "criminoso nato", "criminoso louco", "criminoso habitual", "criminoso passional",
            "criminoso ocasional", "lombroso", "ferri", "garofalo", "atavismo", "estigmas",
            "prognose criminal", "biotipologia", "kretschmer",
        ],
    },
    "4368": {
        "definicao": "Prevenção do delito e modelos de reação ao crime no Estado Democrático de Direito.",
        "termos": [
            "prevencao primaria", "prevencao secundaria", "prevencao terciaria",
            "garcia-pablos de molina", "modelo dissuasorio", "modelo ressocializador",
            "modelo integrador", "justica restaurativa", "reacao social ao delito",
            "policiamento", "populacao carceraria", "reincidencia",
        ],
    },
    "4369": {
        "definicao": "Níveis de prevenção criminal (primária, secundária e terciária) segundo García-Pablos de Molina.",
        "termos": [
            "prevencao primaria", "prevencao secundaria", "prevencao terciaria",
            "causas da criminalidade", "educacao saude trabalho", "setores vulneraveis",
            "policiamento ostensivo", "controle dos meios de comunicacao", "ordenacao urbana",
            "populacao presa", "evitar a reincidencia", "reabilitacao",
        ],
    },
    "4370": {
        "definicao": "Modelos de reação ao delito: clássico/dissuasório, ressocializador e integrador/restaurativo.",
        "termos": [
            "modelo dissuasorio", "modelo classico", "modelo ressocializador",
            "modelo integrador", "justica restaurativa", "mediacao penal",
            "reparacao do dano", "conciliacao",
        ],
    },
    "4371": {
        "definicao": "Evolução histórica do pensamento criminológico: fase pré-científica, Escola Clássica, Escola Positiva e escolas intermediárias.",
        "termos": [
            "escola classica", "escola positiva", "positivismo criminologico",
            "beccaria", "carrara", "livre-arbitrio", "lombroso", "ferri", "garofalo",
            "determinismo", "homem delinquente", "antropologia criminal",
            "terza scuola", "escola de lyon", "defesa social",
        ],
    },
    "4372": {
        "definicao": "Período pré-científico da Criminologia na Antiguidade, Idade Média e Idade Moderna (fisiognomonia, frenologia).",
        "termos": [
            "antiguidade", "idade media", "idade moderna", "fase pre-cientifica",
            "demonologia", "fisiognomonia", "frenologia", "gall", "lavater", "pinel",
        ],
    },
    "4373": {
        "definicao": "Escolas Criminológicas: Escola Clássica, Escola Positiva italiana, Terza Scuola, Escola Moderna Alemã.",
        "termos": [
            "escola classica", "escola positiva", "positivismo criminologico",
            "cesare beccaria", "francesco carrara", "cesare lombroso", "enrico ferri",
            "raffaele garofalo", "livre-arbitrio", "determinismo biologico",
            "sociologia criminal", "delito natural",
        ],
    },
    "4374": {
        "definicao": "Política Criminal, movimentos político-criminais, abolicionismo, minimalismo, garantismo e Direito Penal do Inimigo.",
        "termos": [
            "politica criminal", "direito penal do inimigo", "gunther jakobs",
            "abolicionismo penal", "minimalismo penal", "garantismo penal", "luigi ferrajoli",
            "lei e ordem", "tolerancia zero", "janelas quebradas", "broken windows",
            "velocidades do direito penal", "silva sanchez",
        ],
    },
    "4375": {
        "definicao": "Correntes da Política Criminal: movimentos de Lei e Ordem, Tolerância Zero, Garantismo e Abolicionismo.",
        "termos": [
            "correntes da politica criminal", "movimento de lei e ordem", "tolerancia zero",
            "teoria das janelas quebradas", "abolicionismo", "hulsman", "zafaroni",
            "garantismo penal", "ferrajoli", "direito penal minimo", "ultima ratio",
        ],
    },
    "4376": {
        "definicao": "Direito Penal do Inimigo de Günther Jakobs, terceira velocidade do Direito Penal, antecipação da punibilidade.",
        "termos": [
            "direito penal do inimigo", "gunther jakobs", "cidadao versus inimigo",
            "nao-pessoa", "antecipacao da tutela penal", "periculosidade",
            "terceira velocidade do direito penal", "flexibilizacao de garantias",
        ],
    },
    "4377": {
        "definicao": "Processos de criminalização primária e secundária, seletividade penal e cifras da criminalidade.",
        "termos": [
            "criminalizacao primaria", "criminalizacao secundaria", "cifras criminais",
            "cifra negra", "cifra oculta", "cifra dourada", "cifra amarela", "cifra verde",
            "cifra rosa", "seletividade do sistema penal", "agencias de controle",
        ],
    },
    "4378": {
        "definicao": "Criminalização primária (elaboração legislativa da lei penal) e criminalização secundária (atuação policial e judicial seletiva).",
        "termos": [
            "criminalizacao primaria", "criminalizacao secundaria",
            "definicao legal do crime", "agencias executivas", "policia ministerio publico judiciario",
            "filtro seletivo", "vulnerabilidade",
        ],
    },
    "4379": {
        "definicao": "Cifras criminais: cifra negra (crimes não comunicados/apurados), cifra dourada (colarinho branco), amarela, verde, rosa.",
        "termos": [
            "cifra negra", "cifra dourada", "cifra amarela", "cifra verde", "cifra rosa",
            "subnotificacao", "crimes de colarinho branco", "violencia policial", "crimes ambientais",
        ],
    },
    "4380": {
        "definicao": "Conceito, objeto (delito, delinquente, vítima e controle social), método empírico e interdisciplinar e funções da Criminologia.",
        "termos": [
            "ciencia empirica e interdisciplinar", "delito delinquente vitima controle social",
            "metodo indutivo", "objeto da criminologia", "controle social formal e informal",
            "saber ser", "ciencia causal-explicativa",
        ],
    },
    "4381": {
        "definicao": "Conceito e quádruplo objeto da Criminologia moderna: delito, delinquente, vítima e controle social.",
        "termos": [
            "conceito de criminologia", "objeto da criminologia",
            "delito delinquente vitima e controle social", "controle social formal",
            "controle social informal", "ciencia empirica", "interdisciplinaridade",
        ],
    },
    "4382": {
        "definicao": "Métodos empírico/indutivo e funções da Criminologia na explicação e prevenção do fenômeno criminal.",
        "termos": [
            "metodo empirico", "metodo indutivo", "observacao da realidade",
            "funcoes da criminologia", "compreensao do fenomeno criminal",
        ],
    },
    "4383": {
        "definicao": "Teorias e síndromes vitimológicas: Síndrome de Estocolmo, Síndrome de Londres, Síndrome da Mulher de Potifar.",
        "termos": [
            "sindrome de estocolmo", "sindrome de londres", "mulher de potifar",
            "sindrome de oslo", "desamparo aprendido", "indefensao aprendida",
            "teoria do estilo de vida", "atividades rotineiras",
        ],
    },
    "4384": {
        "definicao": "Teorias legitimadoras da pena: teorias absolutas (retribucionistas), teorias relativas (prevenção geral e especial, positiva e negativa), teoria mista/unificadora e teoria agnóstica/negativa da pena.",
        "termos": [
            "teorias legitimadoras da pena", "finalidades da pena", "teorias absolutas", "teoria retributiva",
            "retribucao", "kant", "hegel", "teorias relativas", "prevencao geral negativa",
            "prevencao geral positiva", "prevencao especial negativa", "prevencao especial positiva",
            "intimidacao", "ressocializacao", "neutralizacao do condenado", "teoria agnostica",
            "feuerbach", "coacao psicologica", "roxin", "teoria mista ou unificadora",
        ],
    },
    "4385": {
        "definicao": "Teorias macrossociológicas do consenso e do conflito explicativas da criminalidade.",
        "termos": [
            "teorias sociologicas da criminalidade", "teorias do consenso", "teorias do conflito",
            "escola de chicago", "ecologia criminal", "associacao diferencial", "edwin sutherland",
            "anomia", "merton", "durkheim", "subcultura delinquente", "albert cohen",
            "labelling approach", "etiquetamento", "reacao social", "howard becker", "ervin goffman",
            "criminologia critica", "criminologia radical", "teoria das janelas quebradas",
            "tecnicas de neutralizacao", "sykes e matza",
        ],
    },
    "4386": {
        "definicao": "Teorias explicativas da criminalidade de nível individual e biopsicológico.",
        "termos": [
            "teorias de nivel individual", "fatores endogenos", "predisposicao genetica",
            "psicopatologia criminal", "personalidade criminosa",
        ],
    },
    "4387": {
        "definicao": "Teorias sociológicas da criminalidade: consenso (Chicago, anomia, associação diferencial, subcultura) e conflito (labelling approach, crítica).",
        "termos": [
            "escola de chicago", "desorganizacao social", "zonas concentricas",
            "associacao diferencial", "sutherland", "crime de colarinho branco", "white collar crime",
            "anomia", "robert merton", "subcultura delinquente", "albert cohen",
            "labelling approach", "etiquetamento", "rotulacao", "howard becker", "lemert",
            "desviacao primaria e secundaria", "criminologia critica", "baratta",
        ],
    },
    "4388": {
        "definicao": "Teorias criminológicas em espécie: associação diferencial, anomia, subcultura delinquente, labelling approach, ecológica.",
        "termos": [
            "associacao diferencial", "sutherland", "anomia", "merton", "subcultura delinquente",
            "cohen", "etiquetamento", "labelling approach", "escola de chicago", "janelas quebradas",
            "neutralizacao", "identidade deteriorada", "estigma",
        ],
    },
    "4389": {
        "definicao": "Vitimologia: estudo científico da vítima, processos de vitimização primária, secundária e terciária, vitimodogmática.",
        "termos": [
            "vitimologia", "vitimizacao primaria", "vitimizacao secundaria", "sobrevitimizacao",
            "revitimizacao", "vitimizacao terciaria", "cifra negra", "vitimodogmatica",
            "autocolocacao em perigo", "assistencia a vitima",
        ],
    },
    "4390": {
        "definicao": "Processo de vitimização: vitimização primária (ofensa direta), secundária (instâncias formais/revitimização) e terciária (falta de amparo social).",
        "termos": [
            "vitimizacao primaria", "vitimizacao secundaria", "sobrevitimizacao",
            "revitimizacao", "vitimizacao terciaria", "processo de vitimizacao",
        ],
    },
    # Penal - Parte Geral e Especial (reforços chave)
    "5071": {
        "definicao": "Concurso de pessoas (arts. 29 a 31 do CP): requisitos, teoria monista, autoria, coautoria, participação, comunicabilidade de circunstâncias.",
        "termos": [
            "concurso de pessoas", "coautoria", "co-autoria", "participacao", "autoria mediata",
            "autoria colateral", "teoria do dominio do fato", "teoria monista",
            "participacao de menor importancia", "cooperacao dolosamente distinta",
            "incomunicabilidade das circunstancias pessoais", "elementares do crime",
            "figurou como participe", "autor e participe", "crimes de mao propria", "crimes unissubsistentes",
        ],
    },
    "5072": {
        "definicao": "Autores e partícipes no concurso de pessoas: conceito restritivo, extensivo e domínio do fato, distinção entre autor e partícipe.",
        "termos": [
            "autores e participes", "figurou como participe", "autor de homicidio",
            "teoria do dominio do fato", "teoria objetivo-formal", "participe do crime",
            "auxilio material", "instigacao", "cumplicidade",
        ],
    },
    "5073": {
        "definicao": "Autoria mediata, autoria colateral, autoria incerta e coautoria (impossibilidade em crimes de mão própria e unissubsistentes).",
        "termos": [
            "autoria mediata", "autoria colateral", "autoria incerta", "coautoria", "co-autoria",
            "co-autoria e impossivel", "crimes de mao propria", "crimes unissubsistentes",
        ],
    },
    "5103": {
        "definicao": "Estupro (art. 213 CP) e estupro de vulnerável (art. 217-A CP), importunação sexual (art. 215-A CP), menor de 14 anos, Súmula 593 STJ.",
        "termos": [
            "estupro", "estupro de vulneravel", "importunacao sexual", "menor de 14 anos",
            "adolescente de 13 anos", "adolescente de 12 anos", "conjuncao carnal", "ato libidinoso",
            "sumula 593", "art 213", "art 217-a", "art 215-a",
        ],
    },
    "5157": {
        "definicao": "Crimes contra o patrimônio (arts. 155 a 183 do CP): furto, roubo, extorsão, dano, apropriação indébita, estelionato, receptação, escusas absolutórias.",
        "termos": [
            "crimes contra o patrimonio", "subtrair para si ou para outrem", "coisa alheia movel",
            "furto", "roubo", "extorsao", "apropriacao indebita", "estelionato", "receptacao",
            "escusas absolutorias", "imunidades patrimoniais", "repouso noturno", "furto privilegiado",
        ],
    },
    "5175": {
        "definicao": "Iter criminis: cogitação, preparação, execução, consumação, crime tentado (art. 14, II CP), desistência voluntária e arrependimento eficaz (art. 15 CP), arrependimento posterior (art. 16 CP), crime impossível (art. 17 CP).",
        "termos": [
            "iter criminis", "crime consumado", "crime tentado", "tentativa", "desistencia voluntaria",
            "arrependimento eficaz", "arrependimento posterior", "crime impossivel",
            "ineficacia absoluta do meio", "impropriedade absoluta do objeto", "circunstancias alheias a vontade",
        ],
    },
    "5180": {
        "definicao": "Lei penal no tempo e no espaço (arts. 1º a 12 do CP): irretroatividade, abolitio criminis, novatio legis in mellius, territorialidade, extraterritorialidade, conflito aparente de normas.",
        "termos": [
            "lei penal no tempo", "lei penal no espaco", "abolitio criminis", "novatio legis",
            "teoria da atividade", "teoria da ubiquidade", "territorialidade", "extraterritorialidade",
            "conflito aparente de normas", "principio da especialidade", "principio da subsidiariedade",
            "principio da consuncao", "principio da alternatividade", "crime progressivo", "progressao criminosa",
            "norma penal em branco", "homovitelina", "heterovitelina",
        ],
    },
    "5183": {
        "definicao": "Conflito aparente de normas penais e princípios solucionadores: especialidade, subsidiariedade, consunção (absorção), alternatividade e normas penais em branco.",
        "termos": [
            "conflito aparente de normas", "principio da especialidade", "principio da subsidiariedade",
            "principio da consuncao", "absorcao", "crime-meio e crime-fim", "antefato impunivel",
            "pos-fato impunivel", "crime progressivo", "norma penal em branco heterogenea", "homovitelina",
        ],
    },
    "5199": {
        "definicao": "Teoria da Pena: penas privativas de liberdade, restritivas de direitos, multa, regimes de cumprimento, dosimetria trifásica (circunstâncias judiciais art. 59, agravantes e atenuantes, causas de aumento e diminuição), sursis, livramento condicional, efeitos da condenação.",
        "termos": [
            "teoria da pena", "dosimetria da pena", "criterio trifasico", "circunstancias judiciais",
            "primeira fase da dosimetria", "segunda fase da dosimetria", "terceira fase da dosimetria",
            "agravantes e atenuantes", "reincidencia", "periodo depurador", "confissao espontanea",
            "efeitos da condenacao", "reparar o dano", "perda de cargo", "regime inicial", "detracao",
        ],
    },
    "5218": {
        "definicao": "Teoria do Crime - Fato Típico: conduta (dolo e culpa), resultado, nexo causal (imputação objetiva, concausas), tipicidade, erro de tipo (art. 20 CP).",
        "termos": [
            "fato tipico", "conduta", "nexo causal", "imputacao objetiva", "concausas",
            "superveniencia de causa relativamente independente", "dolo direto", "dolo eventual",
            "culpa consciente", "erro de tipo", "erro sobre a pessoa", "aberratio ictus",
            "aberratio criminis", "descriminantes putativas", "artigo 20", "art 20",
        ],
    },
    "5224": {
        "definicao": "Erro de tipo essencial e acidental (art. 20 do CP): erro sobre elementos constitutivos do tipo, descriminantes putativas (§ 1º), erro determinado por terceiro (§ 2º), erro sobre a pessoa (§ 3º).",
        "termos": [
            "erro de tipo", "erro sobre elemento constitutivo do tipo", "exclui o dolo",
            "erro sobre a pessoa", "artigo 20", "art 20", "descriminantes putativas",
            "erro vencivel", "erro invencivel", "erro escusavel", "erro inescusavel",
            "qualidades ou condicoes da vitima", "condicoes ou qualidades da vitima",
            "nao sabia da menoridade", "desconhecia a condicao", "desconhecimento da condicao",
            "desconhecer a condicao", "falsa percepcao da realidade",
        ],
    },
    "5228": {
        "definicao": "Ilicitude (antijuridicidade) e causas de exclusão da ilicitude (art. 23 a 25 do CP): estado de necessidade, legítima defesa, estrito cumprimento de dever legal, exercício regular de direito, ofendículos.",
        "termos": [
            "ilicitude", "antijuridicidade", "exclusao da ilicitude", "excludentes de ilicitude",
            "estado de necessidade", "legitima defesa", "estrito cumprimento de dever legal",
            "exercicio regular de direito", "ofendiculo", "ofendiculos", "defesa mecanica predisposta",
            "consentimento do ofendido", "excesso doloso ou culposo",
        ],
    },
    "5211": {
        "definicao": "Culpabilidade: imputabilidade, potencial consciência da ilicitude, exigibilidade de conduta diversa, erro de proibição (art. 21 CP), coação moral irresistível, obediência hierárquica, embriaguez.",
        "termos": [
            "culpabilidade", "imputabilidade", "inimputabilidade", "semi-imputabilidade",
            "potencial consciencia da ilicitude", "erro de proibicao", "exigibilidade de conduta diversa",
            "coacao moral irresistivel", "obediencia hierarquica", "embriaguez acidental completa",
            "actio libera in causa", "menoridade penal",
        ],
    },
    "5100": {
        "definicao": "Crimes de resistência (art. 329 CP), desobediência (art. 330 CP) e desacato (art. 331 CP) praticados por particular contra a administração em geral.",
        "termos": [
            "resistencia", "desobediencia", "desacato", "delito de resistencia",
            "delitos de resistencia", "resistencia qualificada", "impedir que levem sua mercadoria",
            "opor-se a execucao de ato legal", "mediante violencia ou ameaca a funcionario competente",
            "desobedecer a ordem legal", "desacatar funcionario publico", "art 329", "art 330", "art 331",
        ],
    },
    # Processo Penal (reforços chave)
    "5490": {
        "definicao": "Questões e Processos Incidentes no CPP (arts. 92 a 154): questões prejudiciais, exceções (suspeição, impedimento, incompatibilidade, incompetência, litispendência, ilegitimidade), restituição de coisas apreendidas, medidas assecuratórias (sequestro, hipoteca legal, arresto), incidente de falsidade e insanidade mental.",
        "termos": [
            "questoes e processos incidentes", "questoes prejudiciais", "excecao de suspeicao",
            "excecao de impedimento", "incompatibilidade", "juiz nao podera exercer jurisdicao",
            "conjuge ou parente consanguineo ou afim", "restituicao de coisas apreendidas",
            "medidas assecuratorias", "sequestro", "arresto", "hipoteca legal",
            "incidente de falsidade", "incidente de insanidade mental", "art 95", "art 252", "art 254",
        ],
    },
    "5492": {
        "definicao": "Exceção de suspeição, de impedimento ou de incompatibilidade do juiz, membros do MP, peritos e serventuários (arts. 95 a 107 e 252 a 258 do CPP).",
        "termos": [
            "excecao de suspeicao", "excecao de impedimento", "incompatibilidade",
            "juiz nao podera exercer jurisdicao", "conjuge ou parente consanguineo ou afim",
            "amigo intimo ou inimigo capital", "art 252", "art 254",
        ],
    },
    "5498": {
        "definicao": "Inquérito Policial (arts. 4º a 23 do CPP): natureza administrativa, inquisitiva, indisponibilidade, dispensabilidade, prazos de conclusão, arquivamento, acordo de não persecução penal (ANPP, art. 28-A), juiz das garantias.",
        "termos": [
            "inquerito policial", "procedimento administrativo inquisitivo", "autoridade policial",
            "delegado de policia", "arquivamento do inquerito", "acordo de nao persecucao penal",
            "anpp", "juiz das garantias", "indiciamento", "notitia criminis", "art 28-a",
        ],
    },
    "5524": {
        "definicao": "Procedimento do Tribunal do Júri (arts. 406 a 497 do CPP): primeira fase (judicium accusationis / sumário da culpa, arts. 406 a 421), pronúncia, impronúncia, absolvição sumária, desclassificação, segunda fase (judicium causae), desaforamento, quesitação, soberania dos veredictos.",
        "termos": [
            "tribunal do juri", "procedimento do juri", "sumario da culpa", "sumario de culpa",
            "pronuncia", "impronuncia", "pronuncia-lo", "impronuncia-lo",
            "absolvicao sumaria", "desclassificacao", "desaforamento", "conselho de sentenca",
            "quesitos", "soberania dos veredictos", "crimes dolosos contra a vida",
            "judicium accusationis", "judicium causae", "art 406", "art 409", "art 413", "art 414", "art 415", "art 427",
        ],
    },
    "5530": {
        "definicao": "Procedimento comum ordinário (arts. 394 a 405 do CPP): recebimento da denúncia, citação, resposta à acusação em 10 dias, absolvição sumária (art. 397), audiência de instrução e julgamento, memoriais.",
        "termos": [
            "procedimento ordinario", "rito ordinario", "procedimento comum ordinario", "resposta a acusacao",
            "absolvicao sumaria art 397", "audiencia de instrucao e julgamento",
            "pena maxima igual ou superior a 4 anos", "memoriais escritos", "art 394", "art 396", "art 397", "art 400",
        ],
    },
    "5560": {
        "definicao": "Recursos em Espécies no Processo Penal: Recurso em Sentido Estrito (RESE, art. 581 CPP), Apelação (art. 593 CPP), Embargos Infringentes e de Nulidade, Embargos de Declaração, Carta Testemunhável, Correição Parcial, Agravo em Execução, ROC, REsp, RE.",
        "termos": [
            "recurso em sentido estrito", "rese", "recurso de apelacao", "apelacao",
            "embargos infringentes", "embargos de declaracao", "carta testemunhavel",
            "correicao parcial", "agravo em execucao", "em face da referida decisao cabera",
            "art 581", "art 593", "art 609",
        ],
    },
    "5590": {
        "definicao": "Teoria Geral das Provas no Processo Penal (arts. 155 a 157 do CPP): sistemas de avaliação da prova, livre convencimento motivado, princípios relativos à prova penal (autorresponsabilidade, comunhão da prova, audiência contraditória, nemo tenetur se detegere), provas ilícitas, fonte independente, descoberta inevitável, prova emprestada, ônus da prova.",
        "termos": [
            "teoria geral das provas", "principios relativos a prova penal", "provas ilicitas",
            "provas ilicitas por derivacao", "frutos da arvore envenenada", "fonte independente",
            "descoberta inevitavel", "prova emprestada", "onus da prova", "livre convencimento motivado",
            "elementos informativos do inquerito", "contraditorio judicial", "comunhao da prova",
            "art 155", "art 156", "art 157",
        ],
    },
    "4701": {
        "definicao": "Juizado Especial Criminal - JECRIM (Lei nº 9.099/1995) e Procedimento Sumaríssimo: infrações de menor potencial ofensivo (pena máxima até 2 anos), termo circunstanciado, composição dos danos civis, transação penal (art. 76), suspensão condicional do processo (sursis processual, art. 89), turma recursal.",
        "termos": [
            "juizado especial criminal", "juizados especiais criminais", "jecrim", "lei 9099", "lei 9.099",
            "infracao de menor potencial ofensivo", "infracoes de menor potencial ofensivo", "termo circunstanciado",
            "composicao civil dos danos", "composicao dos danos civis", "transacao penal",
            "suspensao condicional do processo", "sursis processual", "procedimento sumarissimo", "turma recursal",
        ],
    },
    "4703": {
        "definicao": "Lei de Execução Penal - LEP (Lei nº 7.210/1984): execução da pena, trabalho do preso, remição da pena por estudo ou trabalho, faltas disciplinares (falta grave, PAD), progressão e regressão de regime, saída temporária, monitoração eletrônica, prisão domiciliar na execução (art. 117), agravo em execução.",
        "termos": [
            "lei de execucao penal", "lep", "lei 7210", "lei 7.210", "execucao penal",
            "remicao da pena", "remicao pelo estudo", "remicao pelo trabalho", "falta grave",
            "progressao de regime", "progressao do regime prisional", "periodo minimo para a progressao",
            "durante a execucao da pena", "regressao de regime", "saida temporaria",
            "agravo em execucao", "juizo da execucao", "estabelecimento penal", "art 112", "art 126",
        ],
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_arquivo(caminho: Path) -> str:
    return sha256_bytes(caminho.read_bytes())


def main() -> None:
    PASTA_ARTEFATOS.mkdir(parents=True, exist_ok=True)
    qs, tax, refs, _ = carregar_anexos(PASTA_DADOS / "anexos")

    # 1. Carrega insumos textuais versionados no próprio repositório (autocontido)
    insumos_path = PASTA_ARTEFATOS / "insumos_base_temas.json"
    insumos = json.loads(insumos_path.read_text(encoding="utf-8"))
    meta_modelo = insumos["meta_modelo"]
    perfis_lista = insumos["perfis"]
    perfis_por_id = {p["tema_id"]: p for p in perfis_lista}
    dic_ancoras = insumos["dicionario_ancoras"]

    # 2. Constrói o catálogo de temas enriquecido + agregação hierárquica por família (nível 1 + filhos nível 2)
    catalogo_nos: dict[str, dict[str, object]] = {}
    for tid in tax.candidatos:
        no = tax.ativos[tid]
        perf = perfis_por_id.get(tid, {})
        comp = ENRIQUECIMENTO_COMPLEMENTAR.get(tid, {})

        definicao_leg = str(perf.get("definicao", "")).strip()
        termos_leg = list(perf.get("termos", []))
        definicao_comp = str(comp.get("definicao", "")).strip()
        termos_comp = list(comp.get("termos", []))

        definicao_final = " ".join(x for x in [definicao_leg, definicao_comp] if x).strip()
        termos_finais = list(dict.fromkeys(termos_leg + termos_comp))

        texto_Proprio = " ".join(
            [no["titulo"]] * 3
            + [no["caminho"], no["descricao"], definicao_final]
            + termos_finais * 2
        ).strip()

        catalogo_nos[tid] = {
            "tema_id": tid,
            "parent_id": no["parent_id"],
            "ramo_pai_nivel1": tax.ramo_pai_nivel1(tid),
            "ramo_canonico": tax.ramo_canonico(tid),
            "disciplina": no["disciplina"],
            "nivel": int(no["nivel"]),
            "titulo": no["titulo"],
            "caminho": no["caminho"],
            "descricao_original": no["descricao"],
            "definicao_enriquecida": definicao_final,
            "termos_canonicos": termos_finais,
            "texto_proprio": texto_Proprio,
        }

    # Agrega os textos e termos dos filhos de nível 2 no ramo canônico de nível 1
    catalogo_ramos: dict[str, dict[str, object]] = {}
    for ramo_id in tax.ramos_canonicos:
        membros = tax.membros_do_ramo(ramo_id)
        no_ramo = catalogo_nos[ramo_id]
        titulos_filhos = [
            catalogo_nos[m]["titulo"] for m in membros if m != ramo_id and m not in MAPA_DUPLICADOS_6700
        ]
        termos_familia: list[str] = []
        definicoes_familia: list[str] = []
        for m in membros:
            if catalogo_nos[m]["definicao_enriquecida"]:
                definicoes_familia.append(str(catalogo_nos[m]["definicao_enriquecida"]))
            for termo in catalogo_nos[m]["termos_canonicos"]:
                if termo not in termos_familia:
                    termos_familia.append(termo)

        texto_familia = " ".join(
            [str(no_ramo["titulo"])] * 4
            + [str(no_ramo["caminho"])] * 2
            + titulos_filhos * 2
            + definicoes_familia
            + termos_familia * 2
        ).strip()

        catalogo_ramos[ramo_id] = {
            "ramo_id": ramo_id,
            "disciplina": no_ramo["disciplina"],
            "titulo": no_ramo["titulo"],
            "caminho": no_ramo["caminho"],
            "membros_ids": membros,
            "titulos_subtemas": titulos_filhos,
            "termos_familia": termos_familia,
            "texto_familia": texto_familia,
        }

    # Incorpora também nos nós individuais de nível 1 o resumo de seus subtemas para reforçar a recuperação
    for ramo_id, info_ramo in catalogo_ramos.items():
        if ramo_id in catalogo_nos:
            catalogo_nos[ramo_id]["texto_familia"] = info_ramo["texto_familia"]
    for tid, info_no in catalogo_nos.items():
        if "texto_familia" not in info_no:
            ramo_id = str(info_no["ramo_canonico"])
            info_no["texto_familia"] = (
                str(info_no["texto_proprio"]) + " " + str(catalogo_ramos[ramo_id]["titulo"])
            ).strip()

    catalogo_completo = {
        "versao": "catalogo-etapa2-v1",
        "total_candidatos_ativos": len(catalogo_nos),
        "total_ramos_canonicos": len(catalogo_ramos),
        "mapa_duplicados_6700": MAPA_DUPLICADOS_6700,
        "mapa_convencao_ramo": MAPA_CONVENCAO_RAMO,
        "normas_legais": dic_ancoras["normas"],
        "siglas_ambiguas": dic_ancoras["siglas_ambiguas"],
        "nos": catalogo_nos,
        "ramos": catalogo_ramos,
    }

    caminho_catalogo = PASTA_ARTEFATOS / "catalogo_temas.json"
    caminho_catalogo.write_text(
        json.dumps(catalogo_completo, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # 3. Valida ou recalcula os vetores de embeddings em cache (.npz comprimido e auditável)
    import sys as _sys
    caminho_npz = PASTA_ARTEFATOS / "embeddings_cache.npz"
    q_ids = [q["id"] for q in qs]
    t_ids = tax.candidatos

    if "--recalcular-embeddings" in _sys.argv or not caminho_npz.exists():
        from fastembed import TextEmbedding
        from processamento import extrair_foco_e_corpo
        embedder = TextEmbedding(model_name=meta_modelo["modelo"])
        textos_q = [extrair_foco_e_corpo(q)["completo"] for q in qs]
        textos_t_orig = [
            f"{tax.ativos[tid]['titulo']} {tax.ativos[tid]['caminho']} {tax.ativos[tid]['descricao']}".strip()
            for tid in t_ids
        ]
        textos_t_perf = [str(catalogo_nos[tid]["texto_proprio"]) for tid in t_ids]
        matriz_questoes = np.stack(list(embedder.embed(textos_q))).astype(np.float32)
        matriz_temas_orig = np.stack(list(embedder.embed(textos_t_orig))).astype(np.float32)
        matriz_temas_perf = np.stack(list(embedder.embed(textos_t_perf))).astype(np.float32)
        np.savez_compressed(
            caminho_npz,
            q_ids=np.array(q_ids),
            t_ids=np.array(t_ids),
            questoes=matriz_questoes,
            temas_orig=matriz_temas_orig,
            temas_perf=matriz_temas_perf,
        )
    else:
        cache_existente = np.load(caminho_npz, allow_pickle=False)
        matriz_questoes = cache_existente["questoes"].astype(np.float32)
        matriz_temas_orig = cache_existente["temas_orig"].astype(np.float32)
        matriz_temas_perf = cache_existente["temas_perf"].astype(np.float32)

    caminho_divisoes = PASTA_ARTEFATOS / "divisoes_validacao.json"
    manifesto = {
        "versao": "etapa2-hibrido-v2",
        "modelo_embedding": meta_modelo["modelo"],
        "licenca_modelo": meta_modelo["licenca"],
        "fastembed_versao": meta_modelo["fastembed"],
        "dimensoes": 384,
        "contagens": {
            "questoes": len(q_ids),
            "temas_candidatos": len(t_ids),
            "ramos_canonicos": len(tax.ramos_canonicos),
            "referencias": len(refs),
        },
        "sha256": {
            "anexos_zip": sha256_arquivo(PASTA_DADOS / "anexos-case-ia.zip"),
            "insumos_base_temas_json": sha256_arquivo(insumos_path),
            "catalogo_temas_json": sha256_arquivo(caminho_catalogo),
            "embeddings_cache_npz": sha256_arquivo(caminho_npz),
            "divisoes_validacao_json": sha256_arquivo(caminho_divisoes),
        },
    }
    caminho_manifesto = PASTA_ARTEFATOS / "manifesto_artefatos.json"
    caminho_manifesto.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] Artefatos gerados com sucesso em: {PASTA_ARTEFATOS}")
    print(f" - catalogo_temas.json ({len(catalogo_nos)} nós, {len(catalogo_ramos)} ramos canônicos)")
    print(f" - embeddings_cache.npz (questões: {matriz_questoes.shape}, temas: {matriz_temas_perf.shape})")


if __name__ == "__main__":
    main()
