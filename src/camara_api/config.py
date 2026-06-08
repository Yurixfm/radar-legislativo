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
