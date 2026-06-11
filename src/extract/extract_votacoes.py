"""Extração de votações e dos votos individuais — tabelas fato `votacoes` e `votos`.

Endpoints:
- GET /votacoes (paginado, filtrado por janela de `data`)
- GET /votacoes/{id}/votos (sub-recurso SEM paginação — ver `client.get_json`)

Para cada votação na janela, buscamos também a lista de votos individuais por
deputado. Isso multiplica o número de chamadas (1 + N por janela); como são
GETs independentes (um por votação), buscamos os votos em paralelo
(`ThreadPoolExecutor`) para não deixar a janela toda escalonada de forma
sequencial.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from src.camara_api.client import CamaraAPIError, get_all_pages, get_json
from src.camara_api.config import dividir_em_janelas, janela_dias
from src.extract.raw_storage import save_raw_json

MAX_WORKERS = 8


def _buscar_votos_votacao(votacao_id) -> list[dict]:
    try:
        payload = get_json(f"/votacoes/{votacao_id}/votos")
    except CamaraAPIError as exc:
        print(f"  [aviso] não foi possível buscar votos da votação {votacao_id}: {exc}")
        return []

    votos = payload.get("dados", [])
    for voto in votos:
        voto["idVotacao"] = votacao_id
    return votos


def extrair_votacoes(
    dias: int = 7,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    buscar_votos: bool = True,
):
    """Busca votações da janela informada e, opcionalmente, os votos de cada uma.

    Retorna `(votacoes, votos)`. Os votos vêm com `idVotacao` anexado
    manualmente, pois o sub-recurso `/votos` não devolve esse identificador
    no corpo da resposta — sem isso seria impossível ligar voto → votação.

    Janelas com mais de 3 meses são divididas automaticamente — a API
    rejeita (HTTP 400) intervalos maiores que isso em /votacoes.
    """
    if not (data_inicio and data_fim):
        data_inicio, data_fim = janela_dias(dias)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    todas_votacoes = []
    todos_votos = []

    for inicio, fim in dividir_em_janelas(data_inicio, data_fim):
        votacoes = get_all_pages(
            "/votacoes",
            params={"dataInicio": inicio, "dataFim": fim, "ordem": "ASC", "ordenarPor": "dataHoraRegistro"},
        )
        caminho_votacoes = save_raw_json("votacoes", f"{inicio}_a_{fim}_{timestamp}", votacoes)
        print(f"[votacoes] {len(votacoes)} registros ({inicio} a {fim}) salvos em {caminho_votacoes}")
        todas_votacoes.extend(votacoes)

        if not buscar_votos:
            continue

        votos = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futuros = [executor.submit(_buscar_votos_votacao, v["id"]) for v in votacoes]
            for futuro in as_completed(futuros):
                votos.extend(futuro.result())

        caminho_votos = save_raw_json("votos", f"{inicio}_a_{fim}_{timestamp}", votos)
        print(f"[votos] {len(votos)} votos individuais salvos em {caminho_votos}")
        todos_votos.extend(votos)

    return todas_votacoes, todos_votos


if __name__ == "__main__":
    extrair_votacoes(dias=7)
