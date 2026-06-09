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


-- Nó 5: Deputados mais ativos (proposições apresentadas na semana)
SELECT
    d.nome,
    d.sigla_partido,
    d.sigla_uf,
    COUNT(*)  AS proposicoes_semana
FROM fato_despesas de
JOIN dim_deputados d ON d.id = de.id_deputado
WHERE de.ano = EXTRACT(YEAR FROM NOW())
  AND de.mes = EXTRACT(MONTH FROM NOW()) - 1
GROUP BY d.nome, d.sigla_partido, d.sigla_uf
ORDER BY proposicoes_semana DESC
LIMIT 5;
