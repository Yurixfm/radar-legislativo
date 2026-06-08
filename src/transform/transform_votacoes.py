"""Transforma o JSON bruto de /votacoes e /votos em DataFrames para
`fato_votacoes` e `votos`.

Projeção (mapa oficial): votações → id, data, dataHoraRegistro, siglaOrgao,
descricao, aprovacao, idProposicao (derivado — ver `_derivar_id_proposicao`);
votos → idVotacao (anexado na extração — o sub-recurso não devolve esse id
sozinho), deputado_.id, tipoVoto, dataRegistroVoto.

`idProposicao` não é um campo direto da API: é derivado de
`uriProposicaoObjeto` (link para `/proposicoes/{id}`, presente na própria
listagem `/votacoes` — sem chamadas extras). Fica NULL quando a votação não
está associada a uma proposição específica (ex.: eleições internas, atas) —
isso ocorre em boa parte das amostras (votações de mesa diretora etc.).
"""
from __future__ import annotations

import re

import pandas as pd

from src.transform.raw_loader import load_latest_raw
from src.transform.validations import deduplicar, exigir_nao_nulos

COLUNAS_VOTACOES = {
    "id": "id",
    "data": "data",
    "dataHoraRegistro": "data_hora_registro",
    "siglaOrgao": "sigla_orgao",
    "descricao": "descricao",
    "aprovacao": "aprovacao",
    "uriProposicaoObjeto": "uri_proposicao_objeto",
}

COLUNAS_VOTOS = {
    "idVotacao": "id_votacao",
    "deputado_.id": "id_deputado",
    "tipoVoto": "tipo_voto",
    "dataRegistroVoto": "data_registro_voto",
}

_RE_ID_NA_URI = re.compile(r"/proposicoes/(\d+)")


def _derivar_id_proposicao(uri: object) -> int | None:
    """Extrai o id numérico de `https://.../proposicoes/{id}`, ou None."""
    if not isinstance(uri, str):
        return None
    encontrado = _RE_ID_NA_URI.search(uri)
    return int(encontrado.group(1)) if encontrado else None


def transformar_votacoes() -> pd.DataFrame:
    registros = load_latest_raw("votacoes")
    df = pd.json_normalize(registros)[list(COLUNAS_VOTACOES)].rename(columns=COLUNAS_VOTACOES)

    df["id_proposicao"] = df["uri_proposicao_objeto"].map(_derivar_id_proposicao).astype("Int64")
    df = df.drop(columns=["uri_proposicao_objeto"])

    df = exigir_nao_nulos(df, ["id", "data"], "votacoes")
    df = deduplicar(df, ["id"], "votacoes")

    return df.reset_index(drop=True)


def transformar_votos() -> pd.DataFrame:
    registros = load_latest_raw("votos")
    if not registros:
        return pd.DataFrame(columns=list(COLUNAS_VOTOS.values()))

    df = pd.json_normalize(registros)[list(COLUNAS_VOTOS)].rename(columns=COLUNAS_VOTOS)

    df = exigir_nao_nulos(df, ["id_votacao", "id_deputado"], "votos")
    df = deduplicar(df, ["id_votacao", "id_deputado"], "votos")

    return df.reset_index(drop=True)


if __name__ == "__main__":
    print(transformar_votacoes().head())
    print(transformar_votos().head())
