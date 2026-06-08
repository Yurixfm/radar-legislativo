"""Extração dos partidos políticos — tabela dimensão `partidos`.

Endpoint: GET /partidos (paginado, ~7-8 registros na legislatura atual).
"""
from __future__ import annotations

from datetime import datetime

from src.camara_api.client import get_all_pages
from src.camara_api.config import LEGISLATURA_ATUAL
from src.extract.raw_storage import save_raw_json


def extrair_partidos(legislatura: int = LEGISLATURA_ATUAL):
    """Busca todos os partidos com representação na legislatura informada."""
    registros = get_all_pages(
        "/partidos",
        params={"idLegislatura": legislatura, "ordem": "ASC", "ordenarPor": "sigla"},
    )

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    caminho = save_raw_json("partidos", f"legislatura{legislatura}_{timestamp}", registros)
    print(f"[partidos] {len(registros)} registros salvos em {caminho}")

    return registros


if __name__ == "__main__":
    extrair_partidos()
