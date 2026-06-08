"""Validações reutilizáveis aplicadas aos DataFrames antes da carga.

Cada função recebe um DataFrame, descarta as linhas que não passam na regra
e IMPRIME um resumo do que foi descartado — a ideia é deixar rastro de
qualidade de dados (quantas linhas, por quê), não falhar silenciosamente nem
derrubar o pipeline por causa de um registro malformado isolado.
"""
from __future__ import annotations

import pandas as pd


def exigir_nao_nulos(df: pd.DataFrame, colunas: list[str], entidade: str) -> pd.DataFrame:
    """Remove linhas com nulo em qualquer uma das `colunas` obrigatórias."""
    validas = df[colunas].notna().all(axis=1)
    descartadas = int((~validas).sum())
    if descartadas:
        print(f"  [validação:{entidade}] descartando {descartadas} linha(s) com campo obrigatório nulo em {colunas}")
    return df[validas].copy()


def exigir_nao_negativos(df: pd.DataFrame, colunas: list[str], entidade: str) -> pd.DataFrame:
    """Remove linhas com valor negativo em qualquer uma das colunas monetárias."""
    validas = (df[colunas].fillna(0) >= 0).all(axis=1)
    descartadas = int((~validas).sum())
    if descartadas:
        print(f"  [validação:{entidade}] descartando {descartadas} linha(s) com valor negativo em {colunas}")
    return df[validas].copy()


def exigir_data_em_intervalo(df: pd.DataFrame, coluna: str, minimo: pd.Timestamp, maximo: pd.Timestamp, entidade: str) -> pd.DataFrame:
    """Remove linhas cuja data em `coluna` esteja fora de [minimo, maximo] (datas absurdas/futuras/nulas)."""
    datas = pd.to_datetime(df[coluna], errors="coerce")
    validas = datas.between(minimo, maximo)
    descartadas = int((~validas).sum())
    if descartadas:
        print(f"  [validação:{entidade}] descartando {descartadas} linha(s) com '{coluna}' fora de [{minimo.date()}, {maximo.date()}] (ou não-parseável)")
    return df[validas].copy()


def deduplicar(df: pd.DataFrame, colunas_chave: list[str], entidade: str) -> pd.DataFrame:
    """Remove duplicatas com base nas colunas que formam a chave primária da tabela."""
    antes = len(df)
    df = df.drop_duplicates(subset=colunas_chave, keep="last")
    removidas = antes - len(df)
    if removidas:
        print(f"  [validação:{entidade}] removendo {removidas} duplicata(s) por chave {colunas_chave}")
    return df
