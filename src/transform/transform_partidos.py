"""Transforma o JSON bruto de /partidos em DataFrame pronto para `dim_partidos`.

Projeção: id, sigla, nome — os únicos campos disponíveis na listagem (campos
como `status`/`numeroEleitoral` exigiriam o detalhe `/partidos/{id}`, uma
chamada extra por partido — pendência documentada no notebook de exploração,
adiada até a análise realmente precisar deles).
"""
from __future__ import annotations

import pandas as pd

from src.transform.raw_loader import load_latest_raw
from src.transform.validations import deduplicar, exigir_nao_nulos


def transformar_partidos() -> pd.DataFrame:
    registros = load_latest_raw("partidos")
    df = pd.json_normalize(registros)[["id", "sigla", "nome"]]

    df = exigir_nao_nulos(df, ["id", "sigla"], "partidos")
    df = deduplicar(df, ["id"], "partidos")

    return df.reset_index(drop=True)


if __name__ == "__main__":
    print(transformar_partidos().head())
