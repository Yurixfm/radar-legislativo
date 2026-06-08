# %% [markdown]
# # Etapa 1 — Exploração da API de Dados Abertos da Câmara dos Deputados
#
# Script no formato "notebook interativo" (células `# %%`, abre direto no
# Jupyter/VS Code). Objetivo: entender o formato de resposta de cada
# endpoint e decidir quais campos importam **antes** de escrever o código
# de extração — curiosidade primeiro, código depois.
#
# - Documentação: https://dadosabertos.camara.leg.br/swagger/api.html
# - Swagger interativo: https://dadosabertos.camara.leg.br/api/v2

# %%
import requests

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

# %% [markdown]
# ## 1. `/deputados` — quem são os 513?

# %%
resp = requests.get(f"{BASE_URL}/deputados", params={"itens": 5, "idLegislatura": 57})
resp.raise_for_status()
payload = resp.json()
payload["dados"][0]

# %% [markdown]
# **Paginação.** A resposta sempre traz uma chave `links` com `self`,
# `next`, `first`, `last`. Cada página tem no máximo 100 itens
# (`itens=100`). Para baixar tudo, é preciso seguir o link `next` num laço
# `while` até ele sumir — é exatamente o que `get_all_pages()`
# (`src/camara_api/client.py`) faz.

# %%
payload["links"]

# %% [markdown]
# **Decisão de campos → dimensão `deputados`**: `id`, `nome`,
# `siglaPartido`, `siglaUf`, `idLegislatura`, `email`, `urlFoto`.
# Descartamos `uri`/`uriPartido` (são links de navegação reconstituíveis a
# partir do `id`).

# %% [markdown]
# ## 2. `/partidos` — dimensão enxuta

# %%
requests.get(f"{BASE_URL}/partidos", params={"itens": 5, "idLegislatura": 57}).json()["dados"][0]

# %% [markdown]
# **Decisão**: `id`, `sigla`, `nome`. Liga com `deputados.siglaPartido` e,
# via autores, com `proposicoes`.

# %% [markdown]
# ## 3. `/proposicoes` — o coração do pipeline

# %%
resp = requests.get(
    f"{BASE_URL}/proposicoes",
    params={
        "dataApresentacaoInicio": "2026-06-01",
        "dataApresentacaoFim": "2026-06-08",
        "itens": 5,
        "ordem": "DESC",
        "ordenarPor": "id",
    },
)
prop = resp.json()["dados"][0]
prop

# %% [markdown]
# **Hipóteses que esse dado responde** (a confirmar nas próximas etapas):
# - Quais temas dominam a pauta numa semana? → precisa da Etapa 4 (IA),
#   pois a API não classifica proposições por tema.
# - Qual tipo de proposição (PL, PEC, REQ, MPV...) é mais comum?
# - Qual a velocidade de tramitação por tipo/órgão?
#
# **Decisão de campos → fato `proposicoes`**: `id`, `siglaTipo`, `numero`,
# `ano`, `ementa`, `dataApresentacao`, `descricaoTipo`,
# `statusProposicao.descricaoSituacao`, `statusProposicao.siglaOrgao`,
# `urlInteiroTeor`. A `ementa` é o campo que alimenta a Etapa 4
# (embeddings/resumo). Descartamos `despacho` (texto longo e repetitivo) e
# `keywords` (quase sempre nulo nas amostras observadas).
#
# **Por que filtrar por data de apresentação?** Sem o filtro, o endpoint
# devolve centenas de milhares de proposições históricas — o erro clássico
# de "querer pegar a API inteira de uma vez". A extração roda em janelas
# curtas e incrementais (7 dias por padrão).

# %% [markdown]
# ## 4. `/votacoes` e `/votacoes/{id}/votos`

# %%
resp = requests.get(
    f"{BASE_URL}/votacoes",
    params={"dataInicio": "2026-06-01", "dataFim": "2026-06-08", "itens": 5},
)
votacao = resp.json()["dados"][0]
votacao

# %%
votos = requests.get(f"{BASE_URL}/votacoes/{votacao['id']}/votos").json()["dados"]
len(votos), votos[:1]

# %% [markdown]
# **Achado importante.** `/votacoes/{id}/votos` **não aceita**
# `itens`/`pagina` — a API responde `400 Parâmetro inválido` se você tentar.
# Ele devolve a lista inteira de uma vez (ou vazia, quando a votação foi
# simbólica/sem registro nominal). Por isso esse sub-recurso usa
# `get_json()` (chamada simples), não `get_all_pages()`.
#
# **Decisão de campos**:
# - `votacoes` (fato): `id`, `data`, `dataHoraRegistro`, `siglaOrgao`,
#   `descricao`, `aprovacao`.
# - `votos` (fato, granularidade deputado×votação): `idVotacao` — que
#   precisamos **anexar manualmente**, pois o sub-recurso não devolve esse
#   id no corpo —, `deputado_.id`, `tipoVoto`, `dataRegistroVoto`.

# %% [markdown]
# ## 5. `/deputados/{id}/despesas` — cota parlamentar

# %%
deputado_id = payload["dados"][0]["id"]
resp = requests.get(
    f"{BASE_URL}/deputados/{deputado_id}/despesas",
    params={"ano": 2026, "itens": 5, "ordem": "DESC"},
)
resp.json()["dados"][0]

# %% [markdown]
# **Decisão de campos → fato `despesas`**: `idDeputado` (anexado
# manualmente — o endpoint é por deputado e não devolve o id no corpo),
# `ano`, `mes`, `tipoDespesa`, `dataDocumento`, `valorDocumento`,
# `valorLiquido`, `valorGlosa`, `nomeFornecedor`, `cnpjCpfFornecedor`.
#
# **Atenção ao volume.** São ~513 deputados × dezenas de notas por mês.
# Buscar despesas de todo mundo no primeiro teste seria o mesmo erro de
# "baixar tudo de uma vez" — por isso a extração (Etapa 2) recebe um
# `limite_deputados` configurável: comece com 10, meça tempo/volume, só
# então amplie.

# %% [markdown]
# ## Resumo das decisões para a Etapa 2 (extração)
#
# | Endpoint | Paginação | Filtro usado | Frequência sugerida |
# |---|---|---|---|
# | `/deputados` | sim (`links.next`) | `idLegislatura=57` | semanal (lista muda pouco) |
# | `/partidos` | sim (`links.next`) | `idLegislatura=57` | semanal |
# | `/proposicoes` | sim (`links.next`) | janela de `dataApresentacao` (7 dias) | diária / incremental |
# | `/votacoes` | sim (`links.next`) | janela de `data` (7 dias) | diária / incremental |
# | `/votacoes/{id}/votos` | **não** (lista única) | — | acoplado à extração de votações |
# | `/deputados/{id}/despesas` | sim (`links.next`) | `ano`/`mes` + `limite_deputados` | mensal, com limite controlado |
