import pendulum

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.empty import EmptyOperator


with DAG(
    dag_id="medistar_pipeline",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    description="Pipeline BDDI do Medistar",
) as dag:

    inicio = EmptyOperator(
        task_id="inicio"
    )

    validar_arquivos = BashOperator(
        task_id="validar_arquivos",
        bash_command="""
        test -f /opt/airflow/data/raw/fonte_1_pacientes_atendimentos.csv &&
        test -f /opt/airflow/data/raw/fonte_2_comunidades_remotas.csv &&
        echo "Arquivos de entrada encontrados."
        """
    )

    configurar_banco = BashOperator(
        task_id="configurar_banco",
        bash_command="""
        cd /opt/airflow &&
        python scripts/setup_database.py
        """
    )

    transformar_dados = BashOperator(
        task_id="transformar_dados",
        bash_command="""
        cd /opt/airflow &&
        python scripts/transform_medistar.py
        """
    )

    carregar_oracle = BashOperator(
        task_id="carregar_oracle",
        bash_command="""
        cd /opt/airflow &&
        python scripts/load_database.py
        """
    )

    validar_saida = BashOperator(
        task_id="validar_saida",
        bash_command="""
        echo "Arquivos gerados em data/silver:" &&
        ls -lh /opt/airflow/data/silver &&
        echo "Arquivos gerados em data/gold:" &&
        ls -lh /opt/airflow/data/gold
        """
    )

    fim = EmptyOperator(
        task_id="fim"
    )

    inicio >> validar_arquivos >> configurar_banco >> transformar_dados >> carregar_oracle >> validar_saida >> fim