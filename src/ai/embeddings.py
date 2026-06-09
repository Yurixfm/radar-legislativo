"""Cliente OpenAI para geração de embeddings — Etapa 4.

Usa text-embedding-3-small: o modelo mais barato da OpenAI para embeddings,
com boa qualidade para textos curtos em português como ementas legislativas.

Preço em junho/2026: U$ 0,020 por 1 milhão de tokens.
Estimativa de custo para 710 proposições (ementa ~80 tokens cada):
  710 × 80 = 56.800 tokens → U$ 0,0011 (menos de 1/10 de centavo de dólar).
"""
from __future__ import annotations

import os

from openai import OpenAI

MODEL = "text-embedding-3-small"
PRICE_USD_PER_1M_TOKENS = 0.020


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY não definida. Adicione ao .env: OPENAI_API_KEY=sk-..."
        )
    return OpenAI(api_key=api_key)


def get_embeddings_batch(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """Gera embeddings para uma lista de textos, em lotes de `batch_size`.

    Retorna os vetores na mesma ordem dos textos de entrada.
    """
    client = _client()
    results: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = client.embeddings.create(input=batch, model=MODEL)
        ordered = sorted(resp.data, key=lambda r: r.index)
        results.extend(r.embedding for r in ordered)
    return results


def estimate_cost(texts: list[str]) -> dict:
    """Estima tokens e custo sem chamar a API.

    Usa ~4 chars/token — conservador para português. Serve para decidir
    se vale a pena rodar antes de confirmar o processamento completo.
    """
    total_chars = sum(len(t) for t in texts)
    est_tokens = total_chars // 4
    est_cost_usd = (est_tokens / 1_000_000) * PRICE_USD_PER_1M_TOKENS
    est_cost_brl = est_cost_usd * 5.80  # câmbio aproximado
    return {
        "n_textos": len(texts),
        "tokens_estimados": est_tokens,
        "custo_usd": est_cost_usd,
        "custo_brl": est_cost_brl,
    }
