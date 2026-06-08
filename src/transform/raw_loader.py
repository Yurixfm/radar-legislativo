"""Localiza e carrega o JSON bruto mais recente de cada entidade extraída.

A extração (Etapa 2) salva um arquivo novo e timestampado a cada execução em
`data/raw/<entidade>/`. A transformação sempre processa o mais recente — é o
"estado atual" da janela incremental mais recentemente baixada da API.
"""
from __future__ import annotations

import json
from pathlib import Path

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


class RawDataNotFoundError(Exception):
    """Não há JSON bruto salvo para a entidade — rode a extração (Etapa 2) primeiro."""


def latest_raw_file(entity: str) -> Path:
    """Retorna o caminho do JSON bruto mais recente da entidade (por data de modificação)."""
    entity_dir = RAW_DATA_DIR / entity
    arquivos = sorted(entity_dir.glob(f"{entity}_*.json"), key=lambda p: p.stat().st_mtime)
    if not arquivos:
        raise RawDataNotFoundError(
            f"Nenhum JSON bruto encontrado em {entity_dir}/. "
            f"Rode `python -m src.extract.extract_{entity}` (ou `run_extraction`) primeiro."
        )
    return arquivos[-1]


def load_latest_raw(entity: str) -> list:
    """Lê o JSON bruto mais recente da entidade e retorna a lista de registros."""
    caminho = latest_raw_file(entity)
    with caminho.open(encoding="utf-8") as fh:
        return json.load(fh)
