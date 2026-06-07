from __future__ import annotations

from radar_legislativo.models import Proposicao
from radar_legislativo.radar import RadarLegislativo


def main() -> None:
    proposicoes = [
        Proposicao(
            identificador="PL 123/2026",
            titulo="Programa de transparencia em compras publicas",
            ementa="Cria regras de publicacao de dados abertos para contratacoes.",
            temas=("transparencia", "dados abertos"),
            urgencia=True,
        ),
        Proposicao(
            identificador="PL 456/2026",
            titulo="Incentivo a educacao digital",
            ementa="Estabelece diretrizes para formacao tecnologica nas escolas.",
            temas=("educacao", "tecnologia"),
        ),
    ]

    radar = RadarLegislativo(["transparencia", "dados", "educacao"])

    for resultado in radar.analisar(proposicoes):
        proposicao = resultado.proposicao
        print(f"{resultado.pontuacao:02d} | {proposicao.identificador} | {proposicao.titulo}")


if __name__ == "__main__":
    main()

