-- Schema do Radar Legislativo — Bússola Pública
-- Aplicado de forma idempotente por src/transform/db.py::aplicar_schema()
-- (todas as instruções usam IF NOT EXISTS — rodar de novo não quebra nada).
--
-- Convenção: nomes de tabela em snake_case (idiomático no Postgres); o
-- "Dim"/"Fato" do mapa de projeção (notebooks/01_exploracao_api.py, seção
-- "Mapa de projeção oficial para a Etapa 3") vira o prefixo dim_/fato_ aqui.

-- ===================== DIMENSÕES =====================

CREATE TABLE IF NOT EXISTS dim_partidos (
    id      INTEGER PRIMARY KEY,
    sigla   TEXT NOT NULL UNIQUE,
    nome    TEXT
);

CREATE TABLE IF NOT EXISTS dim_deputados (
    id              INTEGER PRIMARY KEY,
    nome            TEXT NOT NULL,
    sigla_partido   TEXT,
    sigla_uf        CHAR(2),
    id_legislatura  INTEGER,
    email           TEXT
);

-- Populada pela Etapa 4 (classificação por IA) — fica vazia até lá.
CREATE TABLE IF NOT EXISTS dim_temas (
    id_tema     SERIAL PRIMARY KEY,
    nome_tema   TEXT NOT NULL UNIQUE
);

-- ===================== FATOS =====================

CREATE TABLE IF NOT EXISTS fato_proposicoes (
    id                  BIGINT PRIMARY KEY,
    sigla_tipo          TEXT,
    cod_tipo            INTEGER,
    numero              INTEGER,
    ano                 INTEGER,
    ementa              TEXT,
    data_apresentacao   TIMESTAMP,
    -- preenchidos pela Etapa 4 (camada de IA) — ficam NULL até lá
    id_tema             INTEGER REFERENCES dim_temas(id_tema),
    tema_ia             TEXT,
    resumo_ia           TEXT
);
-- Pendência nº 5 (ver notebooks/01_exploracao_api.py "Mapa de projeção
-- oficial"): situação da tramitação, descrição do tipo e inteiro teor só
-- existem no endpoint de DETALHE (/proposicoes/{id}, ~700 chamadas extras
-- por semana). Decisão: não reservar colunas em branco para isso agora — se
-- um enriquecimento seletivo futuro for implementado, as colunas entram via
-- migração junto com os dados (não antes).

-- Sem FK para dim_proposicoes: a votação pode referenciar uma proposição que
-- não está na janela atual de extração — exigir a FK quebraria a carga.
CREATE TABLE IF NOT EXISTS fato_votacoes (
    id                  TEXT PRIMARY KEY,
    data                DATE,
    data_hora_registro  TIMESTAMP,
    sigla_orgao         TEXT,
    descricao           TEXT,
    aprovacao           SMALLINT,
    -- Derivado de `uriProposicaoObjeto` (ver transform_votacoes.py) — fica
    -- NULL quando a votação não está associada a uma proposição específica.
    id_proposicao       BIGINT
);

-- Grão: 1 linha por (votação, deputado).
--
-- FK só para fato_votacoes: toda votação extraída tem seus votos extraídos
-- na MESMA janela (Etapa 2 busca /votos logo depois de /votacoes), então essa
-- integridade é garantida pelo próprio fluxo de extração.
--
-- Sem FK para dim_deputados: votos podem vir de suplentes que já não estão
-- entre os ~512 "em exercício hoje" capturados em dim_deputados — exigir essa
-- FK quebraria a carga sempre que um suplente aparecesse. Decisão de escopo
-- documentada no README (seção "Modelo de dados").
CREATE TABLE IF NOT EXISTS votos (
    id_votacao          TEXT NOT NULL REFERENCES fato_votacoes(id),
    id_deputado         INTEGER NOT NULL,
    tipo_voto           TEXT,
    data_registro_voto  TIMESTAMP,
    PRIMARY KEY (id_votacao, id_deputado)
);

-- Grão: 1 linha por (deputado, documento fiscal). Sem FK para dim_deputados
-- pelo mesmo motivo de `votos`: despesas de meses passados podem citar
-- deputados que não estão mais em exercício hoje.
CREATE TABLE IF NOT EXISTS despesas (
    id_deputado             INTEGER NOT NULL,
    cod_documento           TEXT NOT NULL,
    ano                     INTEGER,
    mes                     INTEGER,
    tipo_despesa            TEXT,
    data_documento          TIMESTAMP,
    valor_documento         NUMERIC(12, 2),
    valor_liquido           NUMERIC(12, 2),
    valor_glosa             NUMERIC(12, 2),
    nome_fornecedor         TEXT,
    cnpj_cpf_fornecedor     TEXT,
    PRIMARY KEY (id_deputado, cod_documento)
);

-- ===================== MIGRAÇÕES IDEMPOTENTES =====================
-- Evoluções do schema sobre tabelas que já existem em produção (Supabase já
-- estava carregado quando essas mudanças foram decididas). `IF EXISTS`/
-- `IF NOT EXISTS` tornam isso seguro tanto numa base nova quanto numa já
-- populada — pode rodar quantas vezes quiser.

-- Removidas por serem links de navegação/imagem que não agregam à análise.
ALTER TABLE dim_deputados    DROP COLUMN IF EXISTS url_foto;
ALTER TABLE fato_proposicoes DROP COLUMN IF EXISTS uri;

-- Removidas por ficarem permanentemente em branco: só o endpoint de detalhe
-- (/proposicoes/{id}) preenche estes campos — pendência nº 5 (ver acima).
ALTER TABLE fato_proposicoes DROP COLUMN IF EXISTS descricao_tipo;
ALTER TABLE fato_proposicoes DROP COLUMN IF EXISTS descricao_situacao;
ALTER TABLE fato_proposicoes DROP COLUMN IF EXISTS sigla_orgao;
ALTER TABLE fato_proposicoes DROP COLUMN IF EXISTS regime;
ALTER TABLE fato_proposicoes DROP COLUMN IF EXISTS despacho;
ALTER TABLE fato_proposicoes DROP COLUMN IF EXISTS url_inteiro_teor;

-- Adicionada: vínculo votação → proposição, derivado de uriProposicaoObjeto.
ALTER TABLE fato_votacoes ADD COLUMN IF NOT EXISTS id_proposicao BIGINT;
