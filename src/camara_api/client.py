"""Cliente HTTP para a API de Dados Abertos da Câmara dos Deputados.

Cobre os dois padrões observados na exploração (Etapa 1):

1. Endpoints de listagem (`/deputados`, `/proposicoes`, `/votacoes`,
   `/deputados/{id}/despesas`, ...) são paginados em blocos de até 100
   itens e expõem um link `rel=next` em `payload["links"]`. `get_all_pages`
   segue esse link num laço `while` até ele desaparecer.
2. Sub-recursos como `/votacoes/{id}/votos` NÃO aceitam `itens`/`pagina`
   (a API responde 400 "Parâmetro inválido") e devolvem a lista inteira de
   uma vez. Para esses, usamos `get_json`, uma chamada simples.

Erros transitórios (timeout, erro de conexão, 5xx) são tratados com
retentativas e backoff progressivo — erros definitivos (4xx) não são
retentados, pois repetir não muda o resultado.
"""
from __future__ import annotations

import time

import requests

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
DEFAULT_TIMEOUT = 30
DEFAULT_HEADERS = {"Accept": "application/json"}


class CamaraAPIError(Exception):
    """Erro irrecuperável ao consultar a API da Câmara (após retentativas)."""


def _resolve_url(endpoint: str) -> str:
    return endpoint if endpoint.startswith("http") else f"{BASE_URL}{endpoint}"


def _request_with_retry(url, params=None, max_retries=3, backoff_seconds=1.5):
    """Faz GET com retentativa para erros transitórios (timeout/conexão/5xx).

    Erros 4xx (ex.: parâmetro inválido) são propagados imediatamente, pois
    indicam um problema na requisição em si, não algo que vá se resolver
    tentando de novo.
    """
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT)
            if response.status_code >= 500:
                raise requests.HTTPError(f"HTTP {response.status_code} em {response.url}")
            response.raise_for_status()
            return response.json()
        except requests.HTTPError:
            raise
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_exc = exc
            if attempt < max_retries:
                time.sleep(backoff_seconds * attempt)

    raise CamaraAPIError(f"Falha ao consultar {url} após {max_retries} tentativas: {last_exc}") from last_exc


def get_json(endpoint: str, params: dict | None = None):
    """Faz uma única chamada GET e retorna o corpo JSON decodificado.

    Use para sub-recursos que não suportam paginação (ex.: `/votacoes/{id}/votos`).
    """
    try:
        return _request_with_retry(_resolve_url(endpoint), params=params)
    except requests.HTTPError as exc:
        raise CamaraAPIError(f"Erro HTTP ao consultar {endpoint}: {exc}") from exc


def get_all_pages(endpoint: str, params: dict | None = None, page_size: int = 100, sleep_between_pages: float = 0.4):
    """Busca TODOS os registros de um endpoint paginado, seguindo o link `next`.

    A API entrega no máximo `page_size` (até 100) itens por página. Em vez de
    montar `pagina=1, 2, 3...` manualmente, seguimos o link `rel=next` que a
    própria API devolve em `payload["links"]` — ele já vem com a querystring
    completa, então basta repetir o `while` até esse link desaparecer (sinal
    de que chegamos na última página).
    """
    params = dict(params or {})
    params.setdefault("itens", page_size)

    next_url = _resolve_url(endpoint)
    next_params = params
    registros = []

    while next_url:
        try:
            payload = _request_with_retry(next_url, params=next_params)
        except requests.HTTPError as exc:
            raise CamaraAPIError(f"Erro HTTP ao consultar {next_url}: {exc}") from exc

        registros.extend(payload.get("dados", []))

        next_link = next(
            (link["href"] for link in payload.get("links", []) if link.get("rel") == "next"),
            None,
        )
        next_url, next_params = next_link, None  # o link `next` já vem com a querystring montada
        if next_url:
            time.sleep(sleep_between_pages)

    return registros
