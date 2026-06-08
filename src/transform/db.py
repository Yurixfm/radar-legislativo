"""Conexão com o PostgreSQL e aplicação do schema — Etapa 3.

Lê `DATABASE_URL` do `.env` (nunca commitado — veja `.env.example`). Funciona
com qualquer Postgres gerenciado (Supabase, Neon, Railway) ou local, desde
que a connection string use o driver psycopg2 (`postgresql://usuario:senha@host:porta/banco`).
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine

load_dotenv()

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_engine() -> Engine:
    """Cria a engine SQLAlchemy a partir de `DATABASE_URL`.

    Falha cedo com mensagem clara se a variável não estiver definida — melhor
    isso do que deixar o SQLAlchemy estourar um erro de parsing de URL confuso
    lá na frente.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL não definida. Copie .env.example para .env e "
            "preencha com a connection string do seu Postgres (Supabase/Neon/Railway/local)."
        )
    return create_engine(database_url, pool_pre_ping=True)


def aplicar_schema(engine: Engine, schema_path: Path = SCHEMA_PATH) -> None:
    """Executa schema.sql — todas as instruções são `CREATE TABLE IF NOT EXISTS`,
    então rodar isso a cada execução do pipeline é seguro e idempotente."""
    sql = schema_path.read_text(encoding="utf-8")
    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cursor:
            cursor.execute(sql)
        raw_conn.commit()
    finally:
        raw_conn.close()
