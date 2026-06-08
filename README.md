# radar-legislativo

Pipeline de engenharia de dados + IA para a **Bússola Pública** — uma consultoria
fictícia de inteligência legislativa. Em vez de analistas lendo o site da Câmara
dos Deputados o dia inteiro para montar relatórios manuais, este projeto
extrai, organiza, classifica com IA e disponibiliza os dados públicos da
Câmara como produto.

> Desafio Xperiun — Pós em Engenharia de Dados e IA.

## O problema

Hoje, equipes de relações governamentais e jurídico monitoram tramitação,
votações e gastos de parlamentares manualmente: sem base de dados, sem
histórico organizado, com classificação temática inconsistente entre
analistas e alertas que dependem da memória de alguém. Esse pipeline troca
esse processo manual por um fluxo automatizado: **extrai → valida → organiza
→ classifica com IA → alerta**.

Fonte dos dados: [API de Dados Abertos da Câmara dos Deputados](https://dadosabertos.camara.leg.br/swagger/api.html)
(pública, gratuita, atualizada diariamente).

## Status do projeto

- [x] **Etapa 1 — Exploração da API**: mapeamento dos endpoints, formatos de
  resposta e decisões de quais campos usar (ver [`notebooks/01_exploracao_api.py`](notebooks/01_exploracao_api.py)).
- [x] **Etapa 2 — Extração com Python**: scripts que paginam, tratam erros e
  salvam o JSON bruto em disco (ver seção [Como rodar a extração](#como-rodar-a-extração-etapa-2)).
- [ ] Etapa 3 — Transformação com Pandas e carga no PostgreSQL
- [ ] Etapa 4 — Camada de IA (classificação temática / resumo executivo)
- [ ] Etapa 5 — Automação com n8n e apresentação executiva

## Arquitetura da extração (Etapas 1 e 2)

```
src/
├── camara_api/
│   ├── client.py     # GET com retry/backoff + paginação genérica (segue o link "next")
│   └── config.py     # legislatura atual, janelas de data incrementais
└── extract/
    ├── raw_storage.py        # salva o JSON bruto em data/raw/<entidade>/ antes de transformar
    ├── extract_deputados.py  # GET /deputados            → dimensão deputados
    ├── extract_partidos.py   # GET /partidos             → dimensão partidos
    ├── extract_proposicoes.py# GET /proposicoes          → fato proposicoes
    ├── extract_votacoes.py   # GET /votacoes (+ /votos)  → fatos votacoes e votos
    ├── extract_despesas.py   # GET /deputados/{id}/despesas → fato despesas
    └── run_extraction.py     # orquestra as 5 extrações numa única chamada (CLI)

notebooks/
└── 01_exploracao_api.py  # exploração da API em formato notebook (células `# %%`)
```

### Decisões de engenharia (Etapa 1 → 2)

- **Paginação via link `next`, não contagem manual de páginas.** A API
  devolve `payload["links"]` com `rel: next`; o cliente (`get_all_pages`)
  segue esse link num `while` até ele desaparecer — cada página tem até 100
  itens (`itens=100`).
- **`/votacoes/{id}/votos` não pagina.** Esse sub-recurso rejeita
  `itens`/`pagina` (HTTP 400) e devolve a lista completa de uma vez — por
  isso usa uma chamada simples (`get_json`), sem o laço de paginação.
- **Janelas curtas e incrementais, não o histórico inteiro.** `/proposicoes`
  e `/votacoes` sempre são filtradas por data (padrão: últimos 7 dias).
  Sem esse filtro, `/proposicoes` sozinho devolve centenas de milhares de
  registros — o erro clássico de "baixar a API inteira de uma vez".
- **`/deputados/{id}/despesas` é uma chamada por deputado.** Para não
  multiplicar ~513 × N páginas logo de cara, a extração aceita
  `limite_deputados` (padrão: 10) — meça volume/tempo numa amostra antes de
  ampliar.
- **Erros transitórios (timeout, conexão, 5xx) são retentados com backoff
  progressivo; erros 4xx não são** — repetir uma requisição malformada não
  muda o resultado.
- **JSON bruto salvo antes de qualquer transformação**, em
  `data/raw/<entidade>/`. Se o `transform` (Etapa 3) quebrar, a extração não
  precisa rodar de novo.

## Como rodar a extração (Etapa 2)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# roda as 5 extrações com os parâmetros padrão (últimos 7 dias, 10 deputados nas despesas)
python -m src.extract.run_extraction

# exemplos de uso incremental/controlado
python -m src.extract.run_extraction --dias 30 --despesas-limite 20
python -m src.extract.run_extraction --pular-votos --pular-despesas   # só deputados/partidos/proposições/votações
```

Cada execução grava o JSON bruto em `data/raw/<entidade>/` (pasta ignorada
pelo Git — é volumosa e 100% reprodutível a partir da extração). Também é
possível rodar cada extração isoladamente, ex.: `python -m src.extract.extract_proposicoes`.

## Modelo de dados (planejado para a Etapa 3)

- **Dimensões**: `deputados` (id, nome, partido, UF, ...), `partidos` (id, sigla, nome)
- **Fatos**: `proposicoes` (ementa, tipo, situação, ...), `votacoes` (descrição, aprovação, ...),
  `votos` (deputado × votação × tipoVoto), `despesas` (deputado × documento × valor)

O detalhamento de colunas e relacionamentos será documentado quando a Etapa 3
(carga no PostgreSQL) estiver pronta.

## Requisitos

- Python 3.11+
- Dependências em [`requirements.txt`](requirements.txt) (cresce conforme as próximas etapas — Pandas/SQLAlchemy/OpenAI entram nas Etapas 3 e 4)

## Repositório

https://github.com/Yurixfm/radar-legislativo
