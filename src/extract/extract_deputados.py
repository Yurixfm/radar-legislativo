"""Extração da lista de deputados em exercício — tabela dimensão `deputados`.

Endpoint: GET /deputados (paginado, ~512 registros em exercício hoje).

⚠️ Testamos três formas de filtrar e elas devolvem números bem diferentes:
- sem filtro de data → ~512 (a API já assume "em exercício agora") ✅ usamos esta
- `idLegislatura=57` sozinho → ~870 (inclui titulares E suplentes que
  passaram pela Casa em qualquer momento do mandato 2023-2027— não é "quem
  decide hoje")
- `dataInicio=<hoje>` → vazio (o snapshot de status do dia ainda não fechou
  na própria API; só funciona com datas passadas)
A opção sem filtro é a mais simples, mais robusta a esse tipo de
inconsistência de "data de hoje", e a que melhor representa a proposta da
Bússola Pública: "513 deputados decidem o rumo de pautas".
"""
from __future__ import annotations

from datetime import datetime

from src.camara_api.client import get_all_pages
from src.extract.raw_storage import save_raw_json


def extrair_deputados():
    """Busca os deputados em exercício hoje (default da própria API) e salva o JSON bruto."""
    registros = get_all_pages("/deputados", params={"ordem": "ASC", "ordenarPor": "nome"})

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    caminho = save_raw_json("deputados", f"em-exercicio_{timestamp}", registros)
    print(f"[deputados] {len(registros)} registros em exercício salvos em {caminho}")

    return registros


if __name__ == "__main__":
    extrair_deputados()
