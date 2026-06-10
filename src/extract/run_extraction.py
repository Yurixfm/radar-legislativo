"""Orquestra a extração incremental de todas as entidades em uma única chamada.

Uso:
    python -m src.extract.run_extraction
    python -m src.extract.run_extraction --dias 7 --despesas-limite 10
    python -m src.extract.run_extraction --pular-votos --pular-despesas

Cada etapa salva seu próprio JSON bruto em `data/raw/<entidade>/` e segue
rodando mesmo se uma etapa específica falhar — assim um erro pontual (ex.:
timeout nas despesas) não derruba a extração inteira.
"""
from __future__ import annotations

import argparse
from datetime import date

from src.camara_api.client import CamaraAPIError
from src.extract.extract_deputados import extrair_deputados
from src.extract.extract_despesas import extrair_despesas, mes_anterior
from src.extract.extract_partidos import extrair_partidos
from src.extract.extract_proposicoes import extrair_proposicoes
from src.extract.extract_votacoes import extrair_votacoes


def main():
    parser = argparse.ArgumentParser(description="Extração incremental — API de Dados Abertos da Câmara dos Deputados")
    parser.add_argument("--dias", type=int, default=7, help="Janela de dias para proposições/votações (padrão: 7)")
    parser.add_argument("--despesas-limite", type=int, default=10, help="Nº de deputados a considerar nas despesas, para controlar volume/custo (padrão: 10)")
    parser.add_argument("--pular-proposicoes", action="store_true", help="Pula a extração de proposições")
    parser.add_argument("--pular-votos", action="store_true", help="Pula a busca de votos individuais por votação")
    parser.add_argument("--pular-despesas", action="store_true", help="Pula a extração de despesas")
    parser.add_argument("--despesas-ano-todo", action="store_true", help="Busca despesas de todos os meses já fechados do ano corrente (backfill), em vez de só o mês anterior")
    args = parser.parse_args()

    deputados = []

    print("== [1/5] deputados ==")
    try:
        deputados = extrair_deputados()
    except CamaraAPIError as exc:
        print(f"  [erro] extração de deputados falhou: {exc}")

    print("== [2/5] partidos ==")
    try:
        extrair_partidos()
    except CamaraAPIError as exc:
        print(f"  [erro] extração de partidos falhou: {exc}")

    if not args.pular_proposicoes:
        print(f"== [3/5] proposições (últimos {args.dias} dias) ==")
        try:
            extrair_proposicoes(dias=args.dias)
        except CamaraAPIError as exc:
            print(f"  [erro] extração de proposições falhou: {exc}")
    else:
        print("== [3/5] proposições — pulado (--pular-proposicoes) ==")

    print(f"== [4/5] votações + votos (últimos {args.dias} dias) ==")
    try:
        extrair_votacoes(dias=args.dias, buscar_votos=not args.pular_votos)
    except CamaraAPIError as exc:
        print(f"  [erro] extração de votações falhou: {exc}")

    if not args.pular_despesas:
        if args.despesas_ano_todo:
            ano = date.today().year
            print(f"== [5/5] despesas (todos os meses fechados de {ano} — {args.despesas_limite} deputados) ==")
            try:
                extrair_despesas(ano=ano, mes=None, limite_deputados=args.despesas_limite, deputados=deputados or None)
            except CamaraAPIError as exc:
                print(f"  [erro] extração de despesas falhou: {exc}")
        else:
            ano, mes = mes_anterior()
            print(f"== [5/5] despesas ({mes:02d}/{ano} — mês fechado anterior, {args.despesas_limite} deputados) ==")
            try:
                extrair_despesas(ano=ano, mes=mes, limite_deputados=args.despesas_limite, deputados=deputados or None)
            except CamaraAPIError as exc:
                print(f"  [erro] extração de despesas falhou: {exc}")
    else:
        print("== [5/5] despesas — pulado (--pular-despesas) ==")

    print("\nExtração concluída. JSON bruto disponível em data/raw/.")


if __name__ == "__main__":
    main()
