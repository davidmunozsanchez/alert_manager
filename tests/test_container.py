import os
import requests
import pytest
from sqlalchemy import create_engine, text

def test_01_wait_for_database(wait_for, db_dsn):
    def is_db_ready():
        engine = create_engine(db_dsn, connect_args={'connect_timeout': 3})
        with engine.connect() as conn:
            return conn.execute(text("SELECT 1")).scalar() == 1
    wait_for(is_db_ready)

def test_02_airflow_webserver_health(wait_for, airflow_url):
    def is_airflow_ready():
        r = requests.get(airflow_url, timeout=5)
        return r.status_code == 200
    wait_for(is_airflow_ready)