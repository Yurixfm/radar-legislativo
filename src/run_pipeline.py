"""Orquestra o pipeline completo: extração -> transformação/carga -> classificação IA.

Uso:
    python -m src.run_pipeline --backfill    # carga inicial: últimos 90 dias
    python -m src.run_pipeline                # incremental: últimos 7 dias (padrão)
    python -m src.run_pipeline --dias 14       # incremental com janela customizada

90 dias é o limite máximo aceito por chamada nos endpoints /proposicoes e
/votacoes (a API rejeita com HTTP 400 janelas maiores), então `--backfill`
cobre essa janela em uma única consulta por entidade — sem necessidade de
dividir em sub-janelas. A classificação IA roda em modo completo
(`--confirmar`) ao final em ambos os modos — o custo por execução é da ordem
de centavos, proporcional ao nº de proposições novas.
"""
from __future__ import annotations

import argparse
import subprocess
import sys


def _run(args: list[str]) -> None:
    print(f"\n$ {' '.join(args)}")
    subprocess.run(args, check=True)


def main():
    parser = argparse.ArgumentParser(description="Pipeline completo: extração + carga + classificação")
    parser.add_argument("--backfill", action="store_true", help="Carga inicial: extrai os últimos 90 dias (em vez dos 7 dias padrão)")
    parser.add_argument("--dias", type=int, default=7, help="Janela incremental em dias, usada quando --backfill não é passado (padrão: 7)")
    parser.add_argument("--despesas-limite", type=int, default=600, help="Nº de deputados considerados nas despesas (padrão: 600 — cobre todos os ~512 em exercício)")
    args = parser.parse_args()

    py = sys.executable
    dias = 90 if args.backfill else args.dias

    print("== 1/3: extração ==")
    _run([
        py, "-m", "src.extract.run_extraction",
        "--dias", str(dias),
        "--despesas-limite", str(args.despesas_limite),
    ])

    print("\n== 2/3: transformação + carga ==")
    _run([py, "-m", "src.transform.run_transform"])

    print("\n== 3/3: classificação IA ==")
    _run([py, "-m", "src.ai.run_classify", "--confirmar"])

    print("\nPipeline concluído.")


if __name__ == "__main__":
    main()
