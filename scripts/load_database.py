from pathlib import Path
import os

import pandas as pd
import oracledb
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

SILVER_DIR = BASE_DIR / "data" / "silver"
GOLD_DIR = BASE_DIR / "data" / "gold"

COMUNIDADES_PATH = SILVER_DIR / "comunidades_limpas.csv"
ATENDIMENTOS_PATH = SILVER_DIR / "pacientes_limpos.csv"
CLIMA_PATH = SILVER_DIR / "clima_limpo.csv"

TRIAGEM_PATH = GOLD_DIR / "triagem_prioridade.csv"
ALERTAS_PATH = GOLD_DIR / "alertas_comunitarios.csv"

load_dotenv(BASE_DIR / ".env")


def get_connection():
    user = os.getenv("ORACLE_USER")
    password = os.getenv("ORACLE_PASSWORD")
    host = os.getenv("ORACLE_HOST")
    port = os.getenv("ORACLE_PORT")
    sid = os.getenv("ORACLE_SID")

    if not all([user, password, host, port, sid]):
        raise ValueError("Verifique as variáveis ORACLE_USER, ORACLE_PASSWORD, ORACLE_HOST, ORACLE_PORT e ORACLE_SID no arquivo .env")

    dsn = oracledb.makedsn(
        host=host,
        port=int(port),
        sid=sid
    )

    return oracledb.connect(
        user=user,
        password=password,
        dsn=dsn
    )


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    return pd.read_csv(path, encoding="utf-8-sig")


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte NaN para None, porque o Oracle entende None como NULL.
    """
    return df.where(pd.notnull(df), None)


def to_date_column(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    if column_name in df.columns:
        df[column_name] = pd.to_datetime(df[column_name], errors="coerce").dt.date

    return df


def clear_tables(cursor):
    """
    Limpa as tabelas antes de inserir novamente.
    A ordem importa por causa das chaves estrangeiras.
    """
    tables = [
        "TB_ALERTA_COMUNITARIO",
        "TB_TRIAGEM_PRIORIDADE",
        "TB_CLIMA",
        "TB_ATENDIMENTO",
        "TB_COMUNIDADE",
    ]

    for table in tables:
        print(f"Limpando tabela {table}...")
        cursor.execute(f"DELETE FROM {table}")


def insert_comunidades(cursor, df: pd.DataFrame):
    sql = """
        INSERT INTO TB_COMUNIDADE (
            id_comunidade,
            nome_comunidade,
            estado,
            tipo_regiao,
            latitude,
            longitude,
            distancia_hospital_km,
            tempo_deslocamento_min,
            tem_posto_apoio,
            tem_transporte_disponivel,
            barreira_natural,
            nivel_isolamento
        ) VALUES (
            :id_comunidade,
            :nome_comunidade,
            :estado,
            :tipo_regiao,
            :latitude,
            :longitude,
            :distancia_hospital_km,
            :tempo_deslocamento_min,
            :tem_posto_apoio,
            :tem_transporte_disponivel,
            :barreira_natural,
            :nivel_isolamento
        )
    """

    cursor.executemany(sql, df.to_dict("records"))


def insert_atendimentos(cursor, df: pd.DataFrame):
    df = to_date_column(df, "data_atendimento")

    sql = """
        INSERT INTO TB_ATENDIMENTO (
            id_atendimento,
            id_paciente,
            nome_paciente,
            idade,
            sexo,
            id_comunidade,
            data_atendimento,
            sintoma_principal,
            grupo_sintoma,
            temperatura_corporal,
            dias_com_sintomas,
            urgencia_informada_agente
        ) VALUES (
            :id_atendimento,
            :id_paciente,
            :nome_paciente,
            :idade,
            :sexo,
            :id_comunidade,
            :data_atendimento,
            :sintoma_principal,
            :grupo_sintoma,
            :temperatura_corporal,
            :dias_com_sintomas,
            :urgencia_informada_agente
        )
    """

    cursor.executemany(sql, df.to_dict("records"))


def insert_clima(cursor, df: pd.DataFrame):
    df = to_date_column(df, "data_coleta")

    sql = """
        INSERT INTO TB_CLIMA (
            id_comunidade,
            data_coleta,
            chuva_mm,
            temperatura_ambiente,
            velocidade_vento,
            umidade,
            risco_climatico
        ) VALUES (
            :id_comunidade,
            :data_coleta,
            :chuva_mm,
            :temperatura_ambiente,
            :velocidade_vento,
            :umidade,
            :risco_climatico
        )
    """

    cursor.executemany(sql, df.to_dict("records"))


def insert_triagem(cursor, df: pd.DataFrame):
    df = to_date_column(df, "data_processamento")

    sql = """
        INSERT INTO TB_TRIAGEM_PRIORIDADE (
            id_triagem,
            id_atendimento,
            id_comunidade,
            score_clinico,
            score_territorial,
            score_climatico,
            score_total,
            classificacao_prioridade,
            motivo_prioridade,
            data_processamento
        ) VALUES (
            :id_triagem,
            :id_atendimento,
            :id_comunidade,
            :score_clinico,
            :score_territorial,
            :score_climatico,
            :score_total,
            :classificacao_prioridade,
            :motivo_prioridade,
            :data_processamento
        )
    """

    cursor.executemany(sql, df.to_dict("records"))


def insert_alertas(cursor, df: pd.DataFrame):
    if df.empty:
        print("Nenhum alerta comunitário para inserir.")
        return

    df = to_date_column(df, "data_alerta")

    sql = """
        INSERT INTO TB_ALERTA_COMUNITARIO (
            id_alerta,
            id_comunidade,
            grupo_sintoma,
            quantidade_casos,
            periodo_dias,
            nivel_alerta,
            descricao_alerta,
            data_alerta
        ) VALUES (
            :id_alerta,
            :id_comunidade,
            :grupo_sintoma,
            :quantidade_casos,
            :periodo_dias,
            :nivel_alerta,
            :descricao_alerta,
            :data_alerta
        )
    """

    cursor.executemany(sql, df.to_dict("records"))


def main():
    print("Iniciando carga dos dados no Oracle...")

    comunidades = prepare_dataframe(read_csv(COMUNIDADES_PATH))
    atendimentos = prepare_dataframe(read_csv(ATENDIMENTOS_PATH))
    clima = prepare_dataframe(read_csv(CLIMA_PATH))
    triagem = prepare_dataframe(read_csv(TRIAGEM_PATH))
    alertas = prepare_dataframe(read_csv(ALERTAS_PATH))

    connection = get_connection()

    try:
        cursor = connection.cursor()

        clear_tables(cursor)

        print("Inserindo comunidades...")
        insert_comunidades(cursor, comunidades)

        print("Inserindo atendimentos...")
        insert_atendimentos(cursor, atendimentos)

        print("Inserindo clima...")
        insert_clima(cursor, clima)

        print("Inserindo triagens...")
        insert_triagem(cursor, triagem)

        print("Inserindo alertas comunitários...")
        insert_alertas(cursor, alertas)

        connection.commit()

        print("Carga finalizada com sucesso.")

    except Exception as error:
        connection.rollback()
        print("Erro durante a carga. Alterações revertidas.")
        raise error

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()