from unittest import TestCase

from radar_legislativo.models import Proposicao
from radar_legislativo.radar import RadarLegislativo


class RadarLegislativoTest(TestCase):
    def test_prioriza_proposicoes_por_palavra_chave_e_urgencia(self) -> None:
        radar = RadarLegislativo(["transparencia", "educacao"])
        proposicoes = [
            Proposicao(
                identificador="PL 1/2026",
                titulo="Transparencia publica",
                ementa="Amplia dados abertos.",
                temas=("governo",),
                urgencia=True,
            ),
            Proposicao(
                identificador="PL 2/2026",
                titulo="Educacao tecnica",
                ementa="Cria programa de formacao.",
                temas=("educacao",),
            ),
            Proposicao(
                identificador="PL 3/2026",
                titulo="Tema sem relacao",
                ementa="Nao deve aparecer no radar.",
            ),
        ]

        resultados = radar.analisar(proposicoes)

        self.assertEqual(["PL 1/2026", "PL 2/2026"], [r.proposicao.identificador for r in resultados])
        self.assertEqual([15, 10], [r.pontuacao for r in resultados])

