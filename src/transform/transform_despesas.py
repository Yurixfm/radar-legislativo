"""Transforma o JSON bruto de /deputados/{id}/despesas em DataFrame para `despesas`.

Projeção: idDeputado (anexado na extração — o endpoint é por deputado e não
devolve esse id no corpo), codDocumento, ano, mes, tipoDespesa, dataDocumento,
valorDocumento, valorLiquido, valorGlosa, nomeFornecedor, cnpjCpfFornecedor.
"""
from __future__ import annotations

import pandas as pd

from src.transform.raw_loader import load_latest_raw
from src.transform.validations import deduplicar, exigir_nao_negativos, exigir_nao_nulos

COLUNAS = {
    "idDeputado": "id_deputado",
    "codDocumento": "cod_documento",
    "ano": "ano",
    "mes": "mes",
    "tipoDespesa": "tipo_despesa",
    "dataDocumento": "data_documento",
    "valorDocumento": "valor_documento",
    "valorLiquido": "valor_liquido",
    "valorGlosa": "valor_glosa",
    "nomeFornecedor": "nome_fornecedor",
    "cnpjCpfFornecedor": "cnpj_cpf_fornecedor",
}


def transformar_despesas() -> pd.DataFrame:
    registros = load_latest_raw("despesas")
    if not registros:
        return pd.DataFrame(columns=list(COLUNAS.values()))

    df = pd.json_normalize(registros)[list(COLUNAS)].rename(columns=COLUNAS)

    df = exigir_nao_nulos(df, ["id_deputado", "cod_documento"], "despesas")
    df = exigir_nao_negativos(df, ["valor_documento", "valor_liquido"], "despesas")
    df = deduplicar(df, ["id_deputado", "cod_documento"], "despesas")

    return df.reset_index(drop=True)


if __name__ == "__main__":
    print(transformar_despesas().head())
