"""Orquestra a transformação + carga incremental no PostgreSQL — Etapa 3.

Lê o JSON bruto mais recente de cada entidade (salvo pela Etapa 2), aplica
validações com Pandas (campos obrigatórios, datas plausíveis, valores não
negativos, deduplicação) e carrega no Postgres de forma incremental: só
insere linhas cuja chave primária ainda não existe — rodar de novo sobre a
mesma janela não duplica nada.

A ordem dos passos respeita as dependências de FK do schema (dim_partidos e
dim_deputados antes de fato_votacoes/votos; fato_votacoes antes de votos).

Uso:
    python -m src.transform.run_transform
"""
from __future__ import annotations

from src.transform.db import aplicar_schema, get_engine
from src.transform.load import carregar_incremental
from src.transform.raw_loader import RawDataNotFoundError
from src.transform.transform_deputados import transformar_deputados
from src.transform.transform_despesas import transformar_despesas
from src.transform.transform_partidos import transformar_partidos
from src.transform.transform_proposicoes import transformar_proposicoes
from src.transform.transform_votacoes import transformar_votacoes, transformar_votos

PASSOS = [
    ("dim_partidos", transformar_partidos, ["id"]),
    ("dim_deputados", transformar_deputados, ["id"]),
    ("fato_proposicoes", transformar_proposicoes, ["id"]),
    ("fato_votacoes", transformar_votacoes, ["id"]),
    ("votos", transformar_votos, ["id_votacao", "id_deputado"]),
    ("despesas", transformar_despesas, ["id_deputado", "cod_documento"]),
]


def main():
    engine = get_engine()

    print("== aplicando schema (CREATE TABLE IF NOT EXISTS — idempotente) ==")
    aplicar_schema(engine)

    for tabela, transformar, colunas_chave in PASSOS:
        print(f"== {tabela} ==")
        try:
            df = transformar()
        except RawDataNotFoundError as exc:
            print(f"  [aviso] {exc}")
            continue

        carregar_incremental(df, tabela, colunas_chave, engine)

    print("\nTransformação e carga concluídas.")


if __name__ == "__main__":
    main()
