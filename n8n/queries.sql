-- ============================================================
-- Queries usadas no workflow n8n "Radar Legislativo Semanal"
-- Cole cada query no nó Postgres correspondente
-- ============================================================

-- Nó 3: Proposições por tema na última semana
SELECT
    t.nome_tema            AS tema,
    COUNT(*)               AS total,
    STRING_AGG(
        CONCAT(p.sigla_tipo, ' ', p.numero, '/', p.ano, ': ', LEFT(p.ementa, 80)),
        ' | '
        ORDER BY p.data_apresentacao DESC
    ) AS exemplos
FROM fato_proposicoes p
JOIN dim_temas t ON t.id_tema = p.id_tema
WHERE p.data_apresentacao >= NOW() - INTERVAL '7 days'
GROUP BY t.nome_tema
ORDER BY total DESC;


-- Nó 4: Votações recentes (últimos 7 dias)
SELECT
    v.data,
    v.descricao,
    CASE WHEN v.aprovacao = 1 THEN 'APROVADA' ELSE 'REJEITADA' END AS resultado,
    p.sigla_tipo || ' ' || p.numero || '/' || p.ano                AS proposicao,
    p.tema_ia
FROM fato_votacoes v
LEFT JOIN fato_proposicoes p ON p.id = v.id_proposicao
WHERE v.data >= NOW() - INTERVAL '7 days'
ORDER BY v.data DESC
LIMIT 15;


-- Nó 5: Despesas da cota parlamentar (mês anterior)
-- Total gasto por tipo de despesa
SELECT
    de.tipo_despesa,
    COUNT(*)                        AS qtd_documentos,
    SUM(de.valor_liquido)           AS total_liquido,
    ROUND(AVG(de.valor_liquido), 2) AS ticket_medio
FROM fato_despesas de
WHERE de.ano  = EXTRACT(YEAR  FROM NOW() - INTERVAL '1 month')
  AND de.mes  = EXTRACT(MONTH FROM NOW() - INTERVAL '1 month')
GROUP BY de.tipo_despesa
ORDER BY total_liquido DESC
LIMIT 8;


-- Nó 5b: Top 5 deputados por gasto no mês anterior
SELECT
    d.nome,
    d.sigla_partido,
    d.sigla_uf,
    SUM(de.valor_liquido)  AS total_gasto,
    COUNT(*)               AS qtd_documentos
FROM fato_despesas de
JOIN dim_deputados d ON d.id = de.id_deputado
WHERE de.ano  = EXTRACT(YEAR  FROM NOW() - INTERVAL '1 month')
  AND de.mes  = EXTRACT(MONTH FROM NOW() - INTERVAL '1 month')
GROUP BY d.nome, d.sigla_partido, d.sigla_uf
ORDER BY total_gasto DESC
LIMIT 5;
