"""Transforma o JSON bruto de /deputados em DataFrame pronto para `dim_deputados`.

Projeção (decisão registrada em notebooks/01_exploracao_api.py): id, nome,
siglaPartido, siglaUf, idLegislatura, email, urlFoto. Ignoramos `uri`/
`uriPartido` — são links de navegação reconstituíveis a partir do `id`.
"""
from __future__ import annotations

import pandas as pd

from src.transform.raw_loader import load_latest_raw
from src.transform.validations import deduplicar, exigir_nao_nulos

COLUNAS = {
    "id": "id",
    "nome": "nome",
    "siglaPartido": "sigla_partido",
    "siglaUf": "sigla_uf",
    "idLegislatura": "id_legislatura",
    "email": "email",
    "urlFoto": "url_foto",
}


def transformar_deputados() -> pd.DataFrame:
    registros = load_latest_raw("deputados")
    df = pd.json_normalize(registros)[list(COLUNAS)].rename(columns=COLUNAS)

    df = exigir_nao_nulos(df, ["id", "nome"], "deputados")
    df = deduplicar(df, ["id"], "deputados")

    return df.reset_index(drop=True)


if __name__ == "__main__":
    print(transformar_deputados().head())
