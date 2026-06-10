"""Configurações compartilhadas da camada de extração.

Por recomendação do desafio, evitamos baixar o histórico inteiro de uma vez:
o pipeline trabalha com janelas curtas e incrementais (7-30 dias), que podem
ser ampliadas depois que tudo estiver rodando sem quebrar.
"""
from __future__ import annotations

from datetime import date, timedelta

# Legislatura 57 = mandato 2023-2027, a que está em exercício hoje.
LEGISLATURA_ATUAL = 57


def janela_dias(dias: int, fim: date | None = None) -> tuple[str, str]:
    """Retorna (data_inicio, data_fim) em 'YYYY-MM-DD' cobrindo `dias` dias até `fim`.

    `fim` por padrão é hoje. Usado para montar filtros incrementais como
    `dataApresentacaoInicio`/`dataApresentacaoFim` e `dataInicio`/`dataFim`.
    """
    fim = fim or date.today()
    inicio = fim - timedelta(days=dias)
    return inicio.isoformat(), fim.isoformat()


def dividir_em_janelas(data_inicio: str, data_fim: str, max_dias: int = 90) -> list[tuple[str, str]]:
    """Divide [data_inicio, data_fim] em sub-janelas de no máximo `max_dias` dias.

    A API da Câmara rejeita (HTTP 400 — "A diferença entre as datas não pode
    ser maior que 3 meses") janelas maiores que ~3 meses em /proposicoes e
    /votacoes. Esta função garante que cada chamada respeite esse limite,
    permitindo que `--dias` cubra períodos longos (ex.: desde o início do ano).
    """
    inicio = date.fromisoformat(data_inicio)
    fim = date.fromisoformat(data_fim)

    janelas = []
    cursor = inicio
    while cursor < fim:
        proxima = min(cursor + timedelta(days=max_dias), fim)
        janelas.append((cursor.isoformat(), proxima.isoformat()))
        cursor = proxima
    return janelas or [(inicio.isoformat(), fim.isoformat())]
