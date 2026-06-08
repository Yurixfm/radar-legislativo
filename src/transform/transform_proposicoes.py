"""Transforma o JSON bruto de /proposicoes em DataFrame para `fato_proposicoes`.

Projeção: id, siglaTipo, codTipo, numero, ano, ementa, dataApresentacao, uri —
os únicos campos que o endpoint de LISTAGEM (`/proposicoes`, usado na Etapa 2)
realmente devolve.

Pendência documentada (5ª, ver notebooks/01_exploracao_api.py): situação atual
da tramitação (`statusProposicao.*`), `descricaoTipo` e `urlInteiroTeor` só
existem no endpoint de DETALHE (`/proposicoes/{id}`) — exigiriam ~700 chamadas
extras/semana para popular todas as proposições da janela. Decisão: manter
essas colunas como NULL por ora (enriquecimento seletivo fica para uma etapa
futura, ex.: só para as poucas proposições que entram no relatório semanal).

`tema_ia`/`resumo_ia`/`id_tema` também saem como NULL — são preenchidos na
Etapa 4 (IA), que faz UPDATE nessas colunas depois que a proposição já está
carregada.
"""
from __future__ import annotations

import pandas as pd

from src.transform.raw_loader import load_latest_raw
from src.transform.validations import deduplicar, exigir_data_em_intervalo, exigir_nao_nulos

COLUNAS = {
    "id": "id",
    "siglaTipo": "sigla_tipo",
    "codTipo": "cod_tipo",
    "numero": "numero",
    "ano": "ano",
    "ementa": "ementa",
    "dataApresentacao": "data_apresentacao",
    "uri": "uri",
}

# Colunas que só o endpoint de detalhe preenche (pendência nº 5) — ficam NULL
# até existir uma etapa de enriquecimento seletivo.
COLUNAS_PENDENTES_DETALHE = ["descricao_tipo", "descricao_situacao", "sigla_orgao", "regime", "despacho", "url_inteiro_teor"]

# Janela plausível para `data_apresentacao`: 1988 = Constituição Federal
# atual (marco razoável para o acervo digital da Câmara) até "agora". Serve
# para pegar erros óbvios de parsing/data sem descartar registros legítimos.
DATA_MINIMA = pd.Timestamp("1988-01-01")


def transformar_proposicoes() -> pd.DataFrame:
    registros = load_latest_raw("proposicoes")
    df = pd.json_normalize(registros)
    df = df[list(COLUNAS)].rename(columns=COLUNAS)

    df = exigir_nao_nulos(df, ["id", "ementa"], "proposicoes")
    df = exigir_data_em_intervalo(df, "data_apresentacao", DATA_MINIMA, pd.Timestamp.now(), "proposicoes")
    df = deduplicar(df, ["id"], "proposicoes")

    for coluna in COLUNAS_PENDENTES_DETALHE:
        df[coluna] = None

    df["id_tema"] = pd.array([None] * len(df), dtype="Int64")
    df["tema_ia"] = None
    df["resumo_ia"] = None

    return df.reset_index(drop=True)


if __name__ == "__main__":
    print(transformar_proposicoes().head())
