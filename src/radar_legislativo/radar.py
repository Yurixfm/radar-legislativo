from __future__ import annotations

from dataclasses import dataclass

from radar_legislativo.models import Proposicao


@dataclass(frozen=True)
class ResultadoRadar:
    proposicao: Proposicao
    pontuacao: int


class RadarLegislativo:
    def __init__(self, palavras_chave: list[str] | tuple[str, ...]) -> None:
        self.palavras_chave = tuple(p.casefold().strip() for p in palavras_chave if p.strip())

    def analisar(self, proposicoes: list[Proposicao] | tuple[Proposicao, ...]) -> list[ResultadoRadar]:
        resultados = [
            ResultadoRadar(proposicao=proposicao, pontuacao=self._pontuar(proposicao))
            for proposicao in proposicoes
        ]
        relevantes = [resultado for resultado in resultados if resultado.pontuacao > 0]
        return sorted(relevantes, key=lambda item: item.pontuacao, reverse=True)

    def _pontuar(self, proposicao: Proposicao) -> int:
        texto = proposicao.texto_indexado()
        pontos = sum(10 for palavra in self.palavras_chave if palavra in texto)

        if proposicao.urgencia:
            pontos += 5

        return pontos

