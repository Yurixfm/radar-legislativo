"""Extração das despesas da cota parlamentar — tabela fato `despesas`.

Endpoint: GET /deputados/{id}/despesas (paginado), chamado UMA VEZ POR
DEPUTADO e filtrado por ano/mês.

⚠️ Esse é o endpoint mais caro do pipeline: são ~513 deputados, cada um com
sua própria sequência de páginas. Baixar tudo de uma vez no primeiro teste
seria o erro clássico que o desafio pede para evitar — por isso a função
recebe `limite_deputados` (comece com 10, meça o tempo/volume, só então
amplie).
"""
from __future__ import annotations

import time
from datetime import date, datetime

from src.camara_api.client import CamaraAPIError, get_all_pages
from src.extract.extract_deputados import extrair_deputados
from src.extract.raw_storage import save_raw_json


def mes_anterior(referencia: date | None = None) -> tuple[int, int]:
    """Retorna (ano, mes) do mês anterior a `referencia` (hoje, por padrão).

    Notas fiscais da cota parlamentar são processadas com atraso — o mês
    corrente costuma vir vazio (confirmamos isso na exploração: junho/2026
    devolveu 0 registros, enquanto maio/2026 trouxe dados normalmente). Por
    isso o padrão do pipeline é sempre buscar o mês fechado anterior.
    """
    referencia = referencia or date.today()
    if referencia.month == 1:
        return referencia.year - 1, 12
    return referencia.year, referencia.month - 1


def extrair_despesas(ano: int, mes: int | None = None, limite_deputados: int | None = None, deputados=None):
    """Busca despesas da cota parlamentar de cada deputado para `ano`/`mes`.

    `deputados`: lista já extraída (evita rebuscar `/deputados`); se `None`,
    busca a lista completa e aplica `limite_deputados` para cortar o volume.
    """
    if deputados is None:
        deputados = extrair_deputados()
    if limite_deputados:
        deputados = deputados[:limite_deputados]

    params = {"ano": ano, "ordem": "DESC", "ordenarPor": "dataDocumento"}
    if mes:
        params["mes"] = mes

    despesas = []
    for deputado in deputados:
        deputado_id = deputado["id"]
        try:
            registros = get_all_pages(f"/deputados/{deputado_id}/despesas", params=params)
        except CamaraAPIError as exc:
            print(f"  [aviso] falha ao buscar despesas do deputado {deputado_id}: {exc}")
            continue

        for registro in registros:
            registro["idDeputado"] = deputado_id
            despesas.append(registro)

        time.sleep(0.3)

    sufixo_mes = f"{mes:02d}" if mes else "todos-meses"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    caminho = save_raw_json("despesas", f"{ano}-{sufixo_mes}_{len(deputados)}deputados_{timestamp}", despesas)
    print(f"[despesas] {len(despesas)} registros de {len(deputados)} deputados salvos em {caminho}")

    return despesas


if __name__ == "__main__":
    ano, mes = mes_anterior()
    extrair_despesas(ano=ano, mes=mes, limite_deputados=10)
