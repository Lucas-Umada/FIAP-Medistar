from pathlib import Path
import os
import re

import oracledb
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
SQL_PATH = BASE_DIR / "sql" / "create_tables.sql"

load_dotenv(BASE_DIR / ".env")


REQUIRED_TABLES = [
    "TB_COMUNIDADE",
    "TB_ATENDIMENTO",
    "TB_CLIMA",
    "TB_TRIAGEM_PRIORIDADE",
    "TB_ALERTA_COMUNITARIO",
]


def get_connection():
    user = os.getenv("ORACLE_USER")
    password = os.getenv("ORACLE_PASSWORD")
    host = os.getenv("ORACLE_HOST")
    port = os.getenv("ORACLE_PORT")
    sid = os.getenv("ORACLE_SID")

    if not all([user, password, host, port, sid]):
        raise ValueError("Verifique as variáveis do Oracle no arquivo .env")

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


def get_existing_tables(cursor):
    cursor.execute("""
        SELECT table_name
        FROM user_tables
        WHERE table_name IN (
            'TB_COMUNIDADE',
            'TB_ATENDIMENTO',
            'TB_CLIMA',
            'TB_TRIAGEM_PRIORIDADE',
            'TB_ALERTA_COMUNITARIO'
        )
    """)

    return {row[0] for row in cursor.fetchall()}


def split_sql_statements(sql_content):
    statements = []

    for statement in sql_content.split(";"):
        statement = statement.strip()

        if statement:
            statements.append(statement)

    return statements


def get_table_name_from_create(statement):
    match = re.search(
        r"CREATE\s+TABLE\s+([A-Z0-9_]+)",
        statement,
        re.IGNORECASE
    )

    if not match:
        return None

    return match.group(1).upper()


def main():
    print("Iniciando configuração do banco de dados...")

    if not SQL_PATH.exists():
        raise FileNotFoundError(f"Arquivo SQL não encontrado: {SQL_PATH}")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        existing_tables = get_existing_tables(cursor)

        if set(REQUIRED_TABLES).issubset(existing_tables):
            print("Todas as tabelas já existem. Nenhuma criação necessária.")
            return

        sql_content = SQL_PATH.read_text(encoding="utf-8")
        statements = split_sql_statements(sql_content)

        for statement in statements:
            table_name = get_table_name_from_create(statement)

            if table_name and table_name in existing_tables:
                print(f"Tabela {table_name} já existe. Pulando criação.")
                continue

            print(f"Executando criação da tabela {table_name}...")
            cursor.execute(statement)

            if table_name:
                existing_tables.add(table_name)

        connection.commit()
        print("Configuração do banco finalizada com sucesso.")

    except Exception as error:
        connection.rollback()
        print("Erro ao configurar banco. Alterações revertidas.")
        raise error

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()