"""Carga incremental de DataFrames no PostgreSQL — sem duplicar registros já carregados.

Estratégia: para cada tabela, lemos as chaves primárias já presentes no
banco, filtramos o DataFrame para conter só linhas com chave ainda
inexistente, e usamos `DataFrame.to_sql(..., if_exists="append")`. Isso torna
a carga idempotente — rodar o pipeline de novo sobre uma janela já carregada
não duplica nada — sem precisar escrever upsert em SQL bruto.

Pressupõe que o schema (`db.aplicar_schema`) já foi aplicado antes — todas as
tabelas existem no momento da carga.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine, text


def carregar_incremental(df: pd.DataFrame, tabela: str, colunas_chave: list[str], engine: Engine) -> int:
    """Insere em `tabela` somente as linhas de `df` cuja chave ainda não existe.

    Retorna o número de linhas efetivamente inseridas.
    """
    if df.empty:
        print(f"  [carga:{tabela}] nada a carregar (DataFrame vazio)")
        return 0

    chaves_existentes = _chaves_existentes(tabela, colunas_chave, engine)
    novas = _filtrar_novas(df, colunas_chave, chaves_existentes)

    if novas.empty:
        print(f"  [carga:{tabela}] {len(df)} linha(s) recebida(s), todas já existiam — nada novo a inserir")
        return 0

    novas.to_sql(tabela, engine, if_exists="append", index=False, method="multi", chunksize=500)
    print(f"  [carga:{tabela}] {len(novas)} linha(s) nova(s) inserida(s) (de {len(df)} recebida(s))")
    return len(novas)


def _chaves_existentes(tabela: str, colunas_chave: list[str], engine: Engine) -> set[tuple]:
    colunas_sql = ", ".join(colunas_chave)
    with engine.connect() as conn:
        resultado = conn.execute(text(f"SELECT {colunas_sql} FROM {tabela}"))
        return {tuple(row) for row in resultado}


def _filtrar_novas(df: pd.DataFrame, colunas_chave: list[str], chaves_existentes: set[tuple]) -> pd.DataFrame:
    if not chaves_existentes:
        return df
    mask_novas = ~df[colunas_chave].apply(tuple, axis=1).isin(chaves_existentes)
    return df[mask_novas]
