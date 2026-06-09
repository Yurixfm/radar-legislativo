"""Temas para classificação das proposições legislativas.

Cada tema tem uma descrição rica usada para gerar o embedding de referência —
frases curtas mas específicas discriminam melhor do que uma única palavra.
O dicionário é a fonte da verdade: alterar aqui muda automaticamente o que
vai para dim_temas e o que é usado como vetor de comparação.
"""
from __future__ import annotations

TEMAS: dict[str, str] = {
    "Saúde": (
        "Saúde pública, SUS, medicamentos, hospitais, vigilância sanitária, "
        "planos de saúde, vacinação, doenças, profissionais de saúde"
    ),
    "Tributário": (
        "Impostos, tributos, arrecadação, isenção fiscal, ICMS, IR, IPI, "
        "reforma tributária, receita federal, contribuições, desonerações"
    ),
    "Trabalho": (
        "Emprego, trabalhadores, CLT, sindicatos, salário mínimo, "
        "previdência social, aposentadoria, seguro-desemprego, relações trabalhistas"
    ),
    "Tecnologia": (
        "Inovação, tecnologia da informação, inteligência artificial, internet, "
        "startups, telecomunicações, transformação digital, dados, cibersegurança"
    ),
    "Meio Ambiente": (
        "Meio ambiente, mudanças climáticas, desmatamento, sustentabilidade, "
        "energia renovável, poluição, biodiversidade, recursos naturais, licenciamento"
    ),
    "Segurança Pública": (
        "Segurança pública, polícia, crime, drogas, violência, presídios, "
        "legislação penal, combate à corrupção, defesa civil, armamento"
    ),
    "Educação": (
        "Educação, ensino básico e superior, escola, universidade, bolsas, "
        "formação profissional, alfabetização, ENEM, professores, EAD"
    ),
    "Infraestrutura": (
        "Infraestrutura, obras públicas, rodovias, saneamento básico, habitação, "
        "urbanismo, transporte, mobilidade urbana, energia, portos, aeroportos"
    ),
    "Direitos Humanos": (
        "Direitos humanos, igualdade, mulher, criança, idoso, pessoa com deficiência, "
        "inclusão social, assistência social, racismo, violência doméstica"
    ),
    "Administrativo": (
        "Administração pública, servidores públicos, concursos, licitação, "
        "orçamento público, controle externo, gestão governamental, transparência"
    ),
}
