"""Etapa 4 — Classificação temática das proposições por embeddings.

Fluxo:
  1. Popula dim_temas com os 10 temas padrão (idempotente).
  2. Gera embeddings dos 10 temas (referências para comparação).
  3. MODO TESTE (padrão, sem flags):
       - Busca as primeiras 10 proposições sem tema_ia no banco.
       - Classifica e exibe os resultados com o score de similaridade.
       - Exibe a estimativa de custo para classificar TODAS as restantes.
       - Para aqui — nenhum UPDATE é feito no banco.
  4. MODO COMPLETO (--confirmar):
       - Classifica TODAS as proposições sem tema_ia em lotes.
       - UPDATE em fato_proposicoes: preenche id_tema e tema_ia.

Uso:
    python -m src.ai.run_classify                  # modo teste (10 proposições)
    python -m src.ai.run_classify --confirmar       # classifica tudo
    python -m src.ai.run_classify --teste-n 20      # testa com 20 (sem confirmar)
"""
from __future__ import annotations

import argparse

from dotenv import load_dotenv
from sqlalchemy import text

from src.ai.classify import classify
from src.ai.embeddings import estimate_cost, get_embeddings_batch
from src.ai.themes import TEMAS
from src.transform.db import get_engine

load_dotenv()


def _popular_dim_temas(engine) -> dict[str, int]:
    """Insere os temas em dim_temas (ON CONFLICT DO NOTHING) e retorna {nome: id}."""
    with engine.begin() as conn:
        for nome in TEMAS:
            conn.execute(
                text("INSERT INTO dim_temas (nome_tema) VALUES (:nome) ON CONFLICT (nome_tema) DO NOTHING"),
                {"nome": nome},
            )
        rows = conn.execute(text("SELECT id_tema, nome_tema FROM dim_temas")).fetchall()
    return {nome: id_tema for id_tema, nome in rows}


def _buscar_proposicoes_sem_tema(engine, limite: int | None = None) -> list[dict]:
    sql = "SELECT id, ementa FROM fato_proposicoes WHERE tema_ia IS NULL"
    if limite:
        sql += f" ORDER BY id LIMIT {limite}"
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
    return [{"id": r[0], "ementa": r[1] or ""} for r in rows]


def _atualizar_proposicoes(engine, resultados: list[dict]) -> int:
    """UPDATE fato_proposicoes SET id_tema=x, tema_ia=y WHERE id=z."""
    with engine.begin() as conn:
        for r in resultados:
            conn.execute(
                text(
                    "UPDATE fato_proposicoes SET id_tema = :id_tema, tema_ia = :tema_ia "
                    "WHERE id = :id"
                ),
                {"id_tema": r["id_tema"], "tema_ia": r["tema"], "id": r["id"]},
            )
    return len(resultados)


def main():
    parser = argparse.ArgumentParser(description="Etapa 4 — classificação temática por embeddings")
    parser.add_argument("--confirmar", action="store_true", help="Classifica todas as proposições e salva no banco")
    parser.add_argument("--teste-n", type=int, default=10, metavar="N", help="Número de proposições no modo teste (padrão: 10)")
    args = parser.parse_args()

    engine = get_engine()

    # 1. Popula dim_temas
    print("== dim_temas ==")
    tema_ids = _popular_dim_temas(engine)
    print(f"  {len(tema_ids)} temas disponíveis: {', '.join(tema_ids)}")

    # 2. Embeddings dos temas (10 vetores de referência)
    print("\n== embeddings dos temas ==")
    nomes_temas = list(TEMAS.keys())
    descricoes_temas = list(TEMAS.values())
    tema_embeddings_list = get_embeddings_batch(descricoes_temas)
    tema_embeddings: dict[str, list[float]] = dict(zip(nomes_temas, tema_embeddings_list))
    print(f"  {len(tema_embeddings)} embeddings gerados (dimensão: {len(next(iter(tema_embeddings.values())))})")

    # 3. Proposições sem classificação
    total_sem_tema = len(_buscar_proposicoes_sem_tema(engine))
    print(f"\n== proposições sem tema_ia no banco: {total_sem_tema} ==")

    if total_sem_tema == 0:
        print("  Nenhuma proposição para classificar — tudo já está classificado.")
        return

    if not args.confirmar:
        # MODO TESTE
        n = min(args.teste_n, total_sem_tema)
        print(f"\n[MODO TESTE] Classificando {n} proposições para validação...\n")
        proposicoes = _buscar_proposicoes_sem_tema(engine, limite=n)
        ementas = [p["ementa"] for p in proposicoes]
        embeddings = get_embeddings_batch(ementas)

        print(f"{'ID':>12}  {'Tema':20}  {'Score':6}  Ementa (60 chars)")
        print("-" * 90)
        for prop, emb in zip(proposicoes, embeddings):
            tema, score = classify(emb, tema_embeddings)
            ementa_curta = (prop["ementa"] or "")[:60]
            print(f"  {prop['id']:>10}  {tema:20}  {score:.4f}  {ementa_curta}")

        # Estimativa de custo para o lote completo
        restantes = _buscar_proposicoes_sem_tema(engine)
        est = estimate_cost([p["ementa"] for p in restantes])
        print(f"\n{'='*60}")
        print(f"  Estimativa para classificar TODAS as {est['n_textos']} proposições:")
        print(f"  Tokens estimados : ~{est['tokens_estimados']:,}")
        print(f"  Custo estimado   : U$ {est['custo_usd']:.5f}  (~R$ {est['custo_brl']:.4f})")
        print(f"\n  Se os resultados acima parecem corretos, rode:")
        print(f"  python -m src.ai.run_classify --confirmar")
        print(f"{'='*60}")

    else:
        # MODO COMPLETO
        print(f"\n[MODO COMPLETO] Classificando {total_sem_tema} proposições em lotes...")
        proposicoes = _buscar_proposicoes_sem_tema(engine)
        # API rejeita strings vazias — substitui por placeholder para manter alinhamento de índice
        ementas = [p["ementa"] if p["ementa"].strip() else "(sem ementa)" for p in proposicoes]

        est = estimate_cost(ementas)
        print(f"  Custo estimado: U$ {est['custo_usd']:.5f} (~R$ {est['custo_brl']:.4f})")

        embeddings = get_embeddings_batch(ementas, batch_size=100)

        resultados = []
        contagem_temas: dict[str, int] = {}
        for prop, emb in zip(proposicoes, embeddings):
            tema, score = classify(emb, tema_embeddings)
            resultados.append({
                "id": prop["id"],
                "id_tema": tema_ids[tema],
                "tema": tema,
                "score": score,
            })
            contagem_temas[tema] = contagem_temas.get(tema, 0) + 1

        n_atualizadas = _atualizar_proposicoes(engine, resultados)

        print(f"\n  {n_atualizadas} proposições classificadas e salvas.\n")
        print("  Distribuição por tema:")
        for tema, n in sorted(contagem_temas.items(), key=lambda x: -x[1]):
            barra = "█" * (n * 30 // max(contagem_temas.values()))
            print(f"    {tema:22} {n:4}  {barra}")


if __name__ == "__main__":
    main()
