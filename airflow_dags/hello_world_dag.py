from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bas import BashOperator


def _say_hello():
    return "Hello world from Python"


with DAG(
    "hello-world-dag", start_date=datetime(2022, 1, 1), schedule_interval="@daily"
):
    step_1 = PythonOperator(
        task_id="hello_world_python",
        python_callable=_say_hello,
    )
    step_2 = BashOperator(
        task_id="hello_world_bash",
        bash_command="echo 'Hello world from Bash",
    )

    step_1 >> step_2
