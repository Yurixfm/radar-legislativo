"""Classificação temática por similaridade de cosseno — Etapa 4.

Cada proposição recebe o tema cujo embedding de referência tem maior
similaridade de cosseno com o embedding da ementa.
"""
from __future__ import annotations

import numpy as np


def cosine_sim(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a, dtype=np.float32), np.array(b, dtype=np.float32)
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb)))


def classify(
    ementa_embedding: list[float],
    tema_embeddings: dict[str, list[float]],
) -> tuple[str, float]:
    """Retorna (nome_tema, score_cosseno) para o tema mais próximo da ementa."""
    scores = {tema: cosine_sim(ementa_embedding, emb) for tema, emb in tema_embeddings.items()}
    best = max(scores, key=scores.__getitem__)
    return best, round(scores[best], 4)
