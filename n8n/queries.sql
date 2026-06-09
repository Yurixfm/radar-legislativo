-- ============================================================
-- Queries usadas no workflow n8n "Radar Legislativo Semanal"
-- Cole cada query no nó Postgres correspondente
-- ============================================================

-- Nó A: Proposições por tema (última semana)
SELECT
    t.nome_tema                                              AS tema,
    COUNT(*)                                                 AS total,
    STRING_AGG(
        p.sigla_tipo || ' ' || p.numero || '/' || p.ano || ': ' || LEFT(p.ementa, 80),
        ' | ' ORDER BY p.data_apresentacao DESC
    )                                                        AS exemplos
FROM fato_proposicoes p
JOIN dim_temas t ON t.id_tema = p.id_tema
WHERE p.data_apresentacao >= NOW() - INTERVAL '7 days'
GROUP BY t.nome_tema
ORDER BY total DESC;


-- Nó B: Votações recentes com placar (última semana)
SELECT
    v.data,
    v.descricao,
    CASE WHEN v.aprovacao = 1 THEN 'APROVADA' ELSE 'REJEITADA' END AS resultado,
    p.sigla_tipo || ' ' || p.numero || '/' || p.ano                AS proposicao,
    p.tema_ia,
    (SELECT COUNT(*) FROM fato_votos fv
     WHERE fv.id_votacao = v.id AND fv.tipo_voto = 'Sim')          AS votos_sim,
    (SELECT COUNT(*) FROM fato_votos fv
     WHERE fv.id_votacao = v.id AND fv.tipo_voto = 'Não')          AS votos_nao
FROM fato_votacoes v
LEFT JOIN fato_proposicoes p ON p.id = v.id_proposicao
WHERE v.data >= NOW() - INTERVAL '7 days'
ORDER BY v.data DESC
LIMIT 15;


-- Nó C: Posição dos partidos nas votações da semana
-- Como cada partido votou — disciplina e orientação política
SELECT
    d.sigla_partido,
    COUNT(*)                                                      AS total_votos,
    SUM(CASE WHEN fv.tipo_voto = 'Sim'       THEN 1 ELSE 0 END)  AS votos_sim,
    SUM(CASE WHEN fv.tipo_voto = 'Não'       THEN 1 ELSE 0 END)  AS votos_nao,
    SUM(CASE WHEN fv.tipo_voto = 'Abstenção' THEN 1 ELSE 0 END)  AS abstencoes,
    ROUND(
        100.0 * SUM(CASE WHEN fv.tipo_voto = 'Sim' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1
    )                                                             AS pct_favoravel
FROM fato_votos fv
JOIN dim_deputados d  ON d.id  = fv.id_deputado
JOIN fato_votacoes vt ON vt.id = fv.id_votacao
WHERE vt.data >= NOW() - INTERVAL '7 days'
GROUP BY d.sigla_partido
HAVING COUNT(*) >= 5
ORDER BY total_votos DESC
LIMIT 12;


-- Nó D: Despesas por categoria (mês anterior)
SELECT
    de.tipo_despesa                                          AS tipo_despesa,
    COUNT(*)                                                 AS qtd_documentos,
    ROUND(SUM(de.valor_liquido)::numeric, 2)                 AS total_liquido,
    ROUND(AVG(de.valor_liquido)::numeric, 2)                 AS ticket_medio
FROM fato_despesas de
WHERE de.ano = EXTRACT(YEAR  FROM NOW() - INTERVAL '1 month')
  AND de.mes = EXTRACT(MONTH FROM NOW() - INTERVAL '1 month')
GROUP BY de.tipo_despesa
ORDER BY total_liquido DESC
LIMIT 8;


-- Nó E: Top 5 deputados por gasto na cota (mês anterior)
SELECT
    d.nome,
    d.sigla_partido,
    d.sigla_uf,
    ROUND(SUM(de.valor_liquido)::numeric, 2)  AS total_gasto,
    COUNT(*)                                   AS qtd_documentos
FROM fato_despesas de
JOIN dim_deputados d ON d.id = de.id_deputado
WHERE de.ano = EXTRACT(YEAR  FROM NOW() - INTERVAL '1 month')
  AND de.mes = EXTRACT(MONTH FROM NOW() - INTERVAL '1 month')
GROUP BY d.nome, d.sigla_partido, d.sigla_uf
ORDER BY total_gasto DESC
LIMIT 5;
