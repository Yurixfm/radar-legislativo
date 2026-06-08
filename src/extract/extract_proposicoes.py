"""Extração incremental de proposições — tabela fato `proposicoes`.

Endpoint: GET /proposicoes, sempre filtrado por uma janela de
`dataApresentacao`. Sem esse filtro o endpoint devolve centenas de milhares
de registros históricos — exatamente o erro de "baixar a API inteira de uma
vez" que o desafio pede para evitar.
"""
from __future__ import annotations

from datetime import datetime

from src.camara_api.client import get_all_pages
from src.camara_api.config import janela_dias
from src.extract.raw_storage import save_raw_json


def extrair_proposicoes(dias: int = 7, data_inicio: str | None = None, data_fim: str | None = None):
    """Busca proposições apresentadas entre `data_inicio` e `data_fim`.

    Por padrão usa os últimos `dias` dias (7 — comece pequeno e amplie depois
    que o pipeline estiver estável, como recomenda o desafio).
    """
    if not (data_inicio and data_fim):
        data_inicio, data_fim = janela_dias(dias)

    registros = get_all_pages(
        "/proposicoes",
        params={
            "dataApresentacaoInicio": data_inicio,
            "dataApresentacaoFim": data_fim,
            "ordem": "ASC",
            "ordenarPor": "id",
        },
    )

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    caminho = save_raw_json("proposicoes", f"{data_inicio}_a_{data_fim}_{timestamp}", registros)
    print(f"[proposicoes] {len(registros)} registros ({data_inicio} a {data_fim}) salvos em {caminho}")

    return registros


if __name__ == "__main__":
    extrair_proposicoes(dias=7)
