CREATE TABLE TB_COMUNIDADE (
    id_comunidade NUMBER PRIMARY KEY,
    nome_comunidade VARCHAR2(120) NOT NULL,
    estado VARCHAR2(2) NOT NULL,
    tipo_regiao VARCHAR2(50),
    latitude NUMBER(10,6),
    longitude NUMBER(10,6),
    distancia_hospital_km NUMBER(8,2),
    tempo_deslocamento_min NUMBER,
    tem_posto_apoio CHAR(1),
    tem_transporte_disponivel CHAR(1),
    barreira_natural VARCHAR2(80),
    nivel_isolamento VARCHAR2(20)
);

CREATE TABLE TB_ATENDIMENTO (
    id_atendimento NUMBER PRIMARY KEY,
    id_paciente NUMBER NOT NULL,
    nome_paciente VARCHAR2(120) NOT NULL,
    idade NUMBER,
    sexo VARCHAR2(20),
    id_comunidade NUMBER NOT NULL,
    data_atendimento DATE,
    sintoma_principal VARCHAR2(100),
    grupo_sintoma VARCHAR2(50),
    temperatura_corporal NUMBER(4,1),
    dias_com_sintomas NUMBER,
    urgencia_informada_agente VARCHAR2(30),

    CONSTRAINT fk_atendimento_comunidade
        FOREIGN KEY (id_comunidade)
        REFERENCES TB_COMUNIDADE(id_comunidade)
);

CREATE TABLE TB_CLIMA (
    id_comunidade NUMBER NOT NULL,
    data_coleta DATE NOT NULL,
    chuva_mm NUMBER(8,2),
    temperatura_ambiente NUMBER(5,2),
    velocidade_vento NUMBER(6,2),
    umidade NUMBER(5,2),
    risco_climatico VARCHAR2(20),

    CONSTRAINT pk_clima
        PRIMARY KEY (id_comunidade, data_coleta),

    CONSTRAINT fk_clima_comunidade
        FOREIGN KEY (id_comunidade)
        REFERENCES TB_COMUNIDADE(id_comunidade)
);

CREATE TABLE TB_TRIAGEM_PRIORIDADE (
    id_triagem NUMBER PRIMARY KEY,
    id_atendimento NUMBER NOT NULL,
    id_comunidade NUMBER NOT NULL,
    score_clinico NUMBER(6,2),
    score_territorial NUMBER(6,2),
    score_climatico NUMBER(6,2),
    score_total NUMBER(6,2),
    classificacao_prioridade VARCHAR2(50),
    motivo_prioridade VARCHAR2(255),
    data_processamento DATE,

    CONSTRAINT fk_triagem_atendimento
        FOREIGN KEY (id_atendimento)
        REFERENCES TB_ATENDIMENTO(id_atendimento),

    CONSTRAINT fk_triagem_comunidade
        FOREIGN KEY (id_comunidade)
        REFERENCES TB_COMUNIDADE(id_comunidade)
);

CREATE TABLE TB_ALERTA_COMUNITARIO (
    id_alerta NUMBER PRIMARY KEY,
    id_comunidade NUMBER NOT NULL,
    grupo_sintoma VARCHAR2(50),
    quantidade_casos NUMBER,
    periodo_dias NUMBER,
    nivel_alerta VARCHAR2(30),
    descricao_alerta VARCHAR2(255),
    data_alerta DATE,

    CONSTRAINT fk_alerta_comunidade
        FOREIGN KEY (id_comunidade)
        REFERENCES TB_COMUNIDADE(id_comunidade)
);