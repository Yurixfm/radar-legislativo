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

---

## Status do projeto

- [x] **Etapa 1 — Exploração da API**: mapeamento dos endpoints, formatos e campos úteis
- [x] **Etapa 2 — Extração com Python**: paginação, retry/backoff e persistência em JSON bruto
- [x] **Etapa 3 — Transformação e carga no PostgreSQL**: modelo dimensional no Supabase, carga incremental idempotente
- [x] **Etapa 4 — Camada de IA**: classificação temática por embeddings (OpenAI text-embedding-3-small)
- [x] **Etapa 5 — Orquestração**: n8n aciona o pipeline de dados (GitHub Actions) antes de montar o briefing
- [x] **Etapa 6 — Automação com n8n**: briefing semanal gerado automaticamente e entregue por email

---

## Arquitetura geral

```
┌─────────────────────────────────────────────────────┐
│  Etapa 5 — n8n Cloud (Schedule Trigger)             │
│  1. dispara workflow_dispatch no GitHub Actions     │
│  2. aguarda (Wait) o pipeline terminar              │
└──────────────────────┬──────────────────────────────┘
                       │ aciona via API do GitHub
                       ▼
┌─────────────────────────────────────────────────────┐
│  GitHub Actions — pipeline_semanal.yml              │
│  roda `python -m src.run_pipeline` (Etapas 2 a 4)   │
│                                                       │
│  API Câmara (pública)                               │
│        │                                            │
│        ▼                                            │
│  Etapa 2 — Extração                                 │
│  src/extract/  →  data/raw/<entidade>/*.json        │
│        │ JSON bruto completo                        │
│        ▼                                            │
│  Etapa 3 — Transformação                            │
│  src/transform/  →  Supabase (PostgreSQL)           │
│  7 tabelas: dim_* (3) + fato_* (4)                  │
│        │ banco populado                             │
│        ▼                                            │
│  Etapa 4 — IA                                       │
│  src/ai/  →  embeddings + cosine similarity         │
│  classifica proposições em 10 temas                 │
└──────────────────────┬──────────────────────────────┘
                       │ fato_proposicoes.tema_ia preenchido
                       ▼
┌─────────────────────────────────────────────────────┐
│  Etapa 6 — Automação (n8n Cloud)                    │
│  continuação do mesmo workflow da Etapa 5:          │
│  5 queries SQL → Python (contexto) → OpenAI (texto) │
│  → email HTML com análise + tabelas de dados reais  │
└─────────────────────────────────────────────────────┘
```

---

## Pipeline completo (extração + carga + IA)

`src/run_pipeline.py` orquestra as Etapas 2, 3 e 4 numa única chamada — extração,
transformação/carga incremental no Supabase e classificação IA das novas
proposições:

```bash
# carga inicial: últimos 90 dias (limite máximo da API por consulta)
python -m src.run_pipeline --backfill

# incremental: últimos 7 dias (padrão) — uso recorrente/agendado
python -m src.run_pipeline

# janela incremental customizada
python -m src.run_pipeline --dias 14
```

A classificação roda em modo completo (`--confirmar`) ao final de ambos os
modos — o custo é proporcional ao nº de proposições novas (~U$0,02 a cada
~20 mil proposições).

---

## Etapas 1 e 2 — Exploração e Extração

### Estrutura

```
src/
├── camara_api/
│   ├── client.py          # GET com retry/backoff + paginação via link "next"
│   └── config.py          # legislatura atual, janelas de data incrementais
└── extract/
    ├── raw_storage.py         # persiste JSON bruto em data/raw/<entidade>/
    ├── extract_deputados.py   # GET /deputados
    ├── extract_partidos.py    # GET /partidos
    ├── extract_proposicoes.py # GET /proposicoes (janela 7 dias)
    ├── extract_votacoes.py    # GET /votacoes + /votacoes/{id}/votos
    ├── extract_despesas.py    # GET /deputados/{id}/despesas (mês anterior)
    └── run_extraction.py      # CLI que orquestra as 5 extrações

notebooks/
└── 01_exploracao_api.py   # exploração dos endpoints (formato notebook %%cells)
```

### Como rodar

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# extração padrão: últimos 7 dias, 10 deputados nas despesas
python -m src.extract.run_extraction

# ajustes
python -m src.extract.run_extraction --dias 30 --despesas-limite 50
python -m src.extract.run_extraction --pular-votos --pular-despesas
```

### Decisões de engenharia

- **Paginação via link `next`** — segue `payload["links"][rel=next]` num `while`, 100 itens por página.
- **`/votacoes/{id}/votos` não pagina** — rejeita `itens`/`pagina` com 400; usa chamada simples.
- **Janelas incrementais** — `/proposicoes` e `/votacoes` sempre filtradas por data (padrão: 7 dias). Sem filtro retornariam centenas de milhares de registros.
- **JSON bruto antes de transformar** — `data/raw/` salvo antes de qualquer processamento; se o transform quebrar, não reextrai.
- **Retry só em 5xx/timeout** — erros 4xx não são retentados (requisição malformada não muda).

---

## Etapa 3 — Transformação e Carga

### Modelo dimensional

| Tabela | Tipo | Principais colunas |
|---|---|---|
| `dim_partidos` | dimensão | `id`, `sigla`, `nome` |
| `dim_deputados` | dimensão | `id`, `nome`, `sigla_partido`, `sigla_uf`, `id_legislatura`, `email` |
| `dim_temas` | dimensão (IA) | `id_tema`, `nome_tema` |
| `fato_proposicoes` | fato | `id`, `sigla_tipo`, `numero`, `ano`, `ementa`, `data_apresentacao`, `id_tema`, `tema_ia` |
| `fato_votacoes` | fato | `id`, `data`, `descricao`, `aprovacao`, `id_proposicao` |
| `fato_votos` | fato (deputado × votação) | `id_votacao`, `id_deputado`, `tipo_voto` |
| `fato_despesas` | fato (deputado × documento) | `id_deputado`, `ano`, `mes`, `tipo_despesa`, `valor_liquido`, `nome_fornecedor` |

### Estrutura

```
src/transform/
├── schema.sql               # DDL idempotente (IF NOT EXISTS + migrações no topo)
├── db.py                    # get_engine() via SQLAlchemy + psycopg2
├── load.py                  # carregar_incremental() — só insere PKs novas
├── transform_deputados.py
├── transform_partidos.py
├── transform_proposicoes.py # adiciona id_tema, tema_ia como NULL (preenchidos na Etapa 4)
├── transform_votacoes.py    # deriva id_proposicao via regex no uriProposicaoObjeto
├── transform_votacoes_votos.py
├── transform_despesas.py
└── run_transform.py         # CLI que executa todos os passos em sequência
```

### Como rodar

```bash
# cria/atualiza o schema no Supabase e carrega todos os dados extraídos
python -m src.transform.run_transform
```

Requer `.env` com `DATABASE_URL` (pooler do Supabase — porta 6543).

---

## Etapa 4 — Camada de IA

Classifica cada proposição em um de 10 temas usando embeddings semânticos:
`Saúde`, `Tributário`, `Trabalho`, `Tecnologia`, `Meio Ambiente`,
`Segurança Pública`, `Educação`, `Infraestrutura`, `Direitos Humanos`, `Administrativo`.

### Como funciona

1. Gera embeddings dos 10 temas com `text-embedding-3-small` (OpenAI)
2. Gera embedding de cada ementa de proposição
3. Atribui o tema com maior similaridade de cosseno
4. Salva `id_tema` e `tema_ia` em `fato_proposicoes`

### Estrutura

```
src/ai/
├── themes.py       # dicionário {nome_tema: descrição semântica}
├── embeddings.py   # get_embeddings_batch() + estimate_cost()
├── classify.py     # cosine_sim() + classify()
└── run_classify.py # CLI com modo teste (10 props, sem salvar) e --confirmar (tudo)
```

### Como rodar

```bash
# modo teste: classifica 10 proposições e estima custo do lote completo
python -m src.ai.run_classify

# classifica todas as proposições sem tema e salva no banco
python -m src.ai.run_classify --confirmar
```

Requer `OPENAI_API_KEY` no `.env`. Custo típico para ~700 proposições: < U$ 0,01.

---

## Etapa 5 — Orquestração (n8n aciona o pipeline via GitHub Actions)

O workflow do n8n (Etapa 6) só consulta o Supabase — ele não roda Python nem
acessa a API da Câmara diretamente. Para que o briefing semanal sempre
reflita dados atualizados, o **mesmo workflow do n8n** primeiro aciona o
pipeline completo (`src/run_pipeline.py`) via GitHub Actions e só então
segue para as 5 queries SQL.

### Arquivo

```
.github/workflows/pipeline_semanal.yml   # workflow_dispatch -> roda src/run_pipeline.py
```

### Configuração (passo a passo)

**1. Secrets do repositório (GitHub)**

Em `Settings → Secrets and variables → Actions → New repository secret`,
cadastre:

- `DATABASE_URL` — mesma string de conexão do `.env` (pooler do Supabase)
- `OPENAI_API_KEY` — mesma chave do `.env`

**2. Personal Access Token para o n8n**

Em `github.com/settings/tokens` (fine-grained token), gere um token com:

- Repository access: apenas `radar-legislativo`
- Permissions: `Actions` → Read and write

Esse token é usado pelo n8n para chamar a API do GitHub. Guarde-o como
credencial no n8n (Header Auth) — nunca em texto plano no workflow.

**3. Nós novos no início do workflow do n8n**

Inserir entre o **Trigger semanal** e os 5 nós Postgres existentes (Etapa 6):

```
Trigger semanal
   │
   ▼
HTTP Request (POST .../dispatches)
   │
   ▼
Wait (~10-15 min)
   │
   ▼
[5 nós Postgres existentes] → Merge → ... (Etapa 6)
```

- **HTTP Request**:
  - Method: `POST`
  - URL: `https://api.github.com/repos/Yurixfm/radar-legislativo/actions/workflows/pipeline_semanal.yml/dispatches`
  - Authentication: Header Auth (`Authorization: Bearer <PAT>`)
  - Headers extras: `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`
  - Body (JSON): `{ "ref": "main" }`

- **Wait**: a API de dispatch não retorna o status da execução, então o nó
  Wait dá tempo do pipeline terminar antes das queries rodarem (uma extração
  incremental de 7 dias normalmente leva poucos minutos).

### Rodar manualmente (sem n8n)

A action também pode ser disparada manualmente pela aba **Actions** do
GitHub (botão "Run workflow") — útil para testar sem esperar o agendamento.

---

## Etapa 6 — Automação com n8n

Workflow semanal no **n8n Cloud** que gera e envia o briefing automaticamente.

### Arquitetura do workflow

```
Trigger semanal
  ├── Nó A: Proposições por tema (últimos 7 dias)    ──┐
  ├── Nó B: Votações com placar                      ──┤
  ├── Nó C: Posição dos partidos                     ──┼──► Merge (Append) ──► Montar Contexto ──► OpenAI ──► Email
  ├── Nó D: Despesas por categoria (mês anterior)    ──┤
  └── Nó E: Top 5 deputados por gasto                ──┘
```

- **Merge (Append, 5 inputs)** — combina os resultados das 5 queries num único `_items`
- **Montar Contexto (Python)** — discrimina os datasets por campo, gera texto para o prompt e tabelas HTML para o email
- **OpenAI** — gera análise narrativa (máx. 400 palavras) com estrutura obrigatória
- **Email** — análise da IA + 5 tabelas com dados reais diretamente do banco

### Arquivos

```
n8n/
├── queries.sql                  # 5 queries — cole em cada nó Postgres
├── prompt_resumo_executivo.txt  # prompt do nó OpenAI
└── email_template.html          # template HTML do corpo do email
```

### Seções do briefing gerado

1. **Pauta da semana** — temas dominantes e volume de proposições
2. **Votações e placar** — aprovadas/rejeitadas com contagem Sim × Não
3. **Posição dos partidos** — % favorável, votos Sim/Não/Abstenção por partido
4. **Cota parlamentar** — categorias de maior gasto + top 5 deputados do mês
5. **Ponto de atenção** — o que monitorar na próxima semana

---

## Configuração do ambiente

### Variáveis de ambiente (`.env`)

```env
DATABASE_URL=postgresql://postgres.<projeto>:<senha>@aws-1-us-west-2.pooler.supabase.com:6543/postgres
OPENAI_API_KEY=sk-...
```

Copie `.env.example` como ponto de partida. O `.env` é ignorado pelo Git.

### Requisitos

```bash
pip install -r requirements.txt
```

- Python 3.11+
- SQLAlchemy + psycopg2-binary (Supabase)
- openai (embeddings — Etapa 4)
- pandas, python-dotenv, requests

---

## Repositório e infraestrutura

| Recurso | URL |
|---|---|
| Código-fonte | https://github.com/Yurixfm/radar-legislativo |
| Banco de dados (Supabase) | https://supabase.com/dashboard/project/wszwoboaysikoiddpmks |
| API pública do projeto | https://wszwoboaysikoiddpmks.supabase.co |

> O banco requer autenticação para acesso direto. Para avaliação, solicite acesso via convite no Supabase (Settings → Members) ou use as credenciais fornecidas separadamente.
