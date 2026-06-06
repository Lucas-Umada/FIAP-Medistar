SELECT
    classificacao_prioridade,
    COUNT(*) AS total_atendimentos
FROM TB_TRIAGEM_PRIORIDADE
GROUP BY classificacao_prioridade
ORDER BY total_atendimentos DESC;



SELECT
    c.nome_comunidade,
    c.tipo_regiao,
    c.nivel_isolamento,
    ROUND(AVG(t.score_total), 2) AS media_score_total,
    COUNT(t.id_triagem) AS total_atendimentos
FROM TB_TRIAGEM_PRIORIDADE t
JOIN TB_COMUNIDADE c
    ON t.id_comunidade = c.id_comunidade
GROUP BY
    c.nome_comunidade,
    c.tipo_regiao,
    c.nivel_isolamento
ORDER BY media_score_total DESC;



SELECT
    c.nome_comunidade,
    c.tipo_regiao,
    c.distancia_hospital_km,
    c.tempo_deslocamento_min,
    t.classificacao_prioridade,
    COUNT(*) AS total_casos
FROM TB_TRIAGEM_PRIORIDADE t
JOIN TB_COMUNIDADE c
    ON t.id_comunidade = c.id_comunidade
WHERE t.classificacao_prioridade = 'critico territorial'
GROUP BY
    c.nome_comunidade,
    c.tipo_regiao,
    c.distancia_hospital_km,
    c.tempo_deslocamento_min,
    t.classificacao_prioridade
ORDER BY c.distancia_hospital_km DESC;



SELECT
    c.nome_comunidade,
    a.grupo_sintoma,
    COUNT(*) AS total_ocorrencias
FROM TB_ATENDIMENTO a
JOIN TB_COMUNIDADE c
    ON a.id_comunidade = c.id_comunidade
GROUP BY
    c.nome_comunidade,
    a.grupo_sintoma
ORDER BY
    c.nome_comunidade,
    total_ocorrencias DESC;



SELECT
    c.nome_comunidade,
    al.grupo_sintoma,
    al.quantidade_casos,
    al.periodo_dias,
    al.nivel_alerta,
    al.descricao_alerta,
    al.data_alerta
FROM TB_ALERTA_COMUNITARIO al
JOIN TB_COMUNIDADE c
    ON al.id_comunidade = c.id_comunidade
ORDER BY
    al.quantidade_casos DESC,
    al.data_alerta DESC;



SELECT
    cl.risco_climatico,
    t.classificacao_prioridade,
    COUNT(*) AS total_casos,
    ROUND(AVG(cl.chuva_mm), 2) AS media_chuva_mm,
    ROUND(AVG(cl.velocidade_vento), 2) AS media_vento
FROM TB_TRIAGEM_PRIORIDADE t
JOIN TB_CLIMA cl
    ON t.id_comunidade = cl.id_comunidade
GROUP BY
    cl.risco_climatico,
    t.classificacao_prioridade
ORDER BY
    cl.risco_climatico,
    total_casos DESC;



SELECT
    c.nome_comunidade,
    c.tipo_regiao,
    c.distancia_hospital_km,
    c.tempo_deslocamento_min,
    c.tem_transporte_disponivel,
    c.barreira_natural,
    c.nivel_isolamento,
    ROUND(AVG(t.score_territorial), 2) AS media_score_territorial
FROM TB_TRIAGEM_PRIORIDADE t
JOIN TB_COMUNIDADE c
    ON t.id_comunidade = c.id_comunidade
GROUP BY
    c.nome_comunidade,
    c.tipo_regiao,
    c.distancia_hospital_km,
    c.tempo_deslocamento_min,
    c.tem_transporte_disponivel,
    c.barreira_natural,
    c.nivel_isolamento
ORDER BY media_score_territorial DESC;



SELECT
    a.nome_paciente,
    a.idade,
    c.nome_comunidade,
    a.sintoma_principal,
    a.grupo_sintoma,
    a.temperatura_corporal,
    a.dias_com_sintomas,
    t.score_clinico,
    t.score_territorial,
    t.score_climatico,
    t.score_total,
    t.classificacao_prioridade,
    t.motivo_prioridade
FROM TB_TRIAGEM_PRIORIDADE t
JOIN TB_ATENDIMENTO a
    ON t.id_atendimento = a.id_atendimento
JOIN TB_COMUNIDADE c
    ON t.id_comunidade = c.id_comunidade
ORDER BY t.score_total DESC;