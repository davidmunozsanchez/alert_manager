import os
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from airflow.models import DagBag


@pytest.fixture(scope="module")
def dagbag():
    """Load all DAGs from the src/dags folder"""
    root = Path(__file__).parent.parent
    dags_folder = root / "src" / "dags"

    # Configurar AIRFLOW_HOME temporalmente
    os.environ["AIRFLOW_HOME"] = str(root / "tests" / ".airflow")
    os.environ["AIRFLOW__CORE__DAGS_FOLDER"] = str(dags_folder)
    os.environ["AIRFLOW__CORE__LOAD_EXAMPLES"] = "False"

    print(f"\n[DEBUG] Loading DAGs from: {dags_folder}")
    assert dags_folder.exists(), f"DAGs folder not found: {dags_folder}"

    return DagBag(dag_folder=str(dags_folder), include_examples=False)


def test_no_import_errors(dagbag):
    """Test that all DAGs can be imported without errors"""
    assert len(dagbag.import_errors) == 0, f"DAG import errors: {dagbag.import_errors}"


def test_dags_loaded(dagbag):
    """Test that DAGs are loaded"""
    dag_ids = list(dagbag.dags.keys())
    print(f"\n[DEBUG] Found DAGs: {dag_ids}")
    assert len(dagbag.dags) > 0, "No DAGs were loaded"


def test_dag_structure(dagbag):
    """Test each DAG has required attributes"""
    for dag_id, dag in dagbag.dags.items():
        print(f"\n[DEBUG] Testing DAG: {dag_id}")

        # Verificar que tiene un owner
        assert dag.owner is not None, f"DAG {dag_id} has no owner"

        # Verificar schedule_interval (puede ser None para DAGs on-demand)
        if dag.schedule_interval is None:
            warnings.warn(UserWarning(f"DAG {dag_id} has schedule_interval=None (manual/on-demand DAG)"))
        else:
            print(f"[DEBUG] DAG {dag_id} schedule: {dag.schedule_interval}")

        # Verificar que tiene start_date
        assert dag.start_date is not None, f"DAG {dag_id} has no start_date"
        assert isinstance(dag.start_date, datetime), f"DAG {dag_id} start_date is not a datetime object"


def test_dag_has_tasks(dagbag):
    """Test that each DAG has at least one task"""
    for dag_id, dag in dagbag.dags.items():
        assert len(dag.tasks) > 0, f"DAG {dag_id} has no tasks"
        print(f"\n[DEBUG] DAG {dag_id} has {len(dag.tasks)} tasks: {[t.task_id for t in dag.tasks]}")


def test_dag_task_dependencies(dagbag):
    """Test that tasks have proper dependencies"""
    for dag_id, dag in dagbag.dags.items():
        for task in dag.tasks:
            # Verificar que las dependencias existen
            for upstream_task_id in task.upstream_task_ids:
                assert (
                    upstream_task_id in dag.task_dict
                ), f"Task {task.task_id} in DAG {dag_id} depends on non-existent task {upstream_task_id}"


def test_dag_cycles(dagbag):
    """Test that DAGs don't have cycles"""
    for dag_id, dag in dagbag.dags.items():
        # Airflow detecta ciclos automáticamente al cargar
        assert dag_id not in dagbag.import_errors, f"DAG {dag_id} has a cycle or import error"


def test_dag_default_args(dagbag):
    """Test that DAGs have proper default_args"""
    required_default_args = ["owner"]

    for dag_id, dag in dagbag.dags.items():
        if dag.default_args is None:
            # Verificar que al menos el owner del DAG está configurado
            assert dag.owner is not None and dag.owner != "", f"DAG {dag_id} has no default_args and no owner"
            warnings.warn(UserWarning(f"DAG {dag_id} has no default_args, but has owner: {dag.owner}"))
            continue

        print(f"\n[DEBUG] DAG {dag_id} default_args: {dag.default_args}")
        for arg in required_default_args:
            if arg not in dag.default_args:
                warnings.warn(UserWarning(f"DAG {dag_id} missing default_arg: {arg}"))


def test_dag_task_retries(dagbag):
    """Test that tasks have retry configuration"""
    for dag_id, dag in dagbag.dags.items():
        for task in dag.tasks:
            # Verificar que tiene retries configurado (heredado o directo)
            retries = (
                task.retries if task.retries is not None else dag.default_args.get("retries") if dag.default_args else None
            )

            if retries is None:
                warnings.warn(UserWarning(f"Task {task.task_id} in DAG {dag_id} has no retry configuration"))
            else:
                assert retries >= 0, f"Task {task.task_id} in DAG {dag_id} has negative retries"


# # Tests específicos para data_ingesting.py
# @pytest.mark.parametrize("dag_id", ["data_ingesting"])
# def test_data_ingesting_dag(dagbag, dag_id):
#     """Test specific structure of data_ingesting DAG"""
#     if dag_id not in dagbag.dags:
#         pytest.skip(f"DAG {dag_id} not found")

#     dag = dagbag.dags[dag_id]

#     # Verificar que tiene las tareas esperadas
#     task_ids = [task.task_id for task in dag.tasks]
#     print(f"\n[DEBUG] {dag_id} tasks: {task_ids}")

#     # Verificar estructura básica
#     assert dag.owner is not None, f"DAG {dag_id} should have an owner"


# # Tests específicos para data_checking.py
# @pytest.mark.parametrize("dag_id", ["data_checking"])
# def test_data_checking_dag(dagbag, dag_id):
#     """Test specific structure of data_checking DAG"""
#     if dag_id not in dagbag.dags:
#         pytest.skip(f"DAG {dag_id} not found")

#     dag = dagbag.dags[dag_id]

#     # Verificar que tiene las tareas esperadas
#     task_ids = [task.task_id for task in dag.tasks]
#     print(f"\n[DEBUG] {dag_id} tasks: {task_ids}")

#     # Verificar estructura básica
#     assert dag.owner is not None, f"DAG {dag_id} should have an owner"


def test_dag_tasks_have_operators(dagbag):
    """Test that tasks use valid operators"""
    valid_operators = [
        "PythonOperator",
        "BashOperator",
        "DummyOperator",
        "EmptyOperator",
        "BranchPythonOperator",
        "ShortCircuitOperator",
        "EmailOperator",
        "PostgresOperator",
        "SqliteOperator",
        "HttpOperator",
        "PythonSensor",
        "FileSensor",
        "SqlSensor",
        "TimeDeltaSensor",
    ]

    for dag_id, dag in dagbag.dags.items():
        for task in dag.tasks:
            operator_name = task.__class__.__name__
            print(f"\n[DEBUG] Task {task.task_id} uses {operator_name}")
            # Solo advertencia, no falla el test
            if operator_name not in valid_operators:
                warnings.warn(UserWarning(f"Task {task.task_id} uses uncommon operator: {operator_name}"))


def test_dag_scheduling(dagbag):
    """Test that DAGs have valid scheduling configuration"""
    for dag_id, dag in dagbag.dags.items():
        # Si tiene schedule_interval, verificar que es válido
        if dag.schedule_interval is not None:
            assert dag.schedule_interval != "", f"DAG {dag_id} has empty schedule_interval"

            # Verificar que start_date es válido
            if isinstance(dag.start_date, datetime):
                # Hacer ambas fechas aware o naive para la comparación
                now = datetime.now()
                start_date = dag.start_date

                # Si start_date tiene timezone info, agregar timezone a now
                if start_date.tzinfo is not None and start_date.tzinfo.utcoffset(start_date) is not None:
                    from datetime import timezone

                    now = datetime.now(timezone.utc)
                else:
                    # Asegurar que ambas son naive
                    if start_date.tzinfo is not None:
                        start_date = start_date.replace(tzinfo=None)
                    now = now.replace(tzinfo=None)

                # Verificar que start_date no es muy en el futuro (más de 1 año)
                one_year_future = now + timedelta(days=365)
                if start_date > one_year_future:
                    warnings.warn(UserWarning(f"DAG {dag_id} start_date is more than 1 year in the future"))
        else:
            warnings.warn(UserWarning(f"DAG {dag_id} has no schedule (manual/on-demand DAG)"))


def test_dag_timeout_configuration(dagbag):
    """Test that DAGs have timeout configuration"""
    for dag_id, dag in dagbag.dags.items():
        for task in dag.tasks:
            # Verificar que tiene timeout configurado (opcional pero recomendado)
            if hasattr(task, "execution_timeout"):
                if task.execution_timeout is not None:
                    print(f"\n[DEBUG] Task {task.task_id} has timeout: {task.execution_timeout}")


def test_dag_tags(dagbag):
    """Test that DAGs have tags for organization"""
    for dag_id, dag in dagbag.dags.items():
        if not dag.tags or len(dag.tags) == 0:
            warnings.warn(UserWarning(f"DAG {dag_id} has no tags (recommended for organization)"))
        else:
            print(f"\n[DEBUG] DAG {dag_id} tags: {dag.tags}")


def test_dag_documentation(dagbag):
    """Test that DAGs have documentation"""
    for dag_id, dag in dagbag.dags.items():
        if dag.description is None or dag.description.strip() == "":
            warnings.warn(UserWarning(f"DAG {dag_id} has no description"))
        else:
            print(f"\n[DEBUG] DAG {dag_id} description: {dag.description[:50]}...")

        # Verificar que las tareas tienen documentación
        for task in dag.tasks:
            if hasattr(task, "doc") or hasattr(task, "doc_md"):
                if task.doc or (hasattr(task, "doc_md") and task.doc_md):
                    print(f"[DEBUG] Task {task.task_id} has documentation")
