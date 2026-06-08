"""Persistência do JSON bruto retornado pela API, antes de qualquer transformação.

Por quê salvar antes de transformar? Porque se o `transform` (Etapa 3) quebrar
ou precisar de ajustes, não é necessário chamar a API de novo — a extração
roda uma vez, e a transformação pode ser repetida quantas vezes for preciso
a partir do disco.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def save_raw_json(entity: str, filename_suffix: str, payload: Any) -> Path:
    """Salva `payload` em `data/raw/<entity>/<entity>_<filename_suffix>.json`."""
    entity_dir = RAW_DATA_DIR / entity
    entity_dir.mkdir(parents=True, exist_ok=True)

    out_path = entity_dir / f"{entity}_{filename_suffix}.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    return out_path
