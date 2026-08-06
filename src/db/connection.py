"""Database connection helpers shared by the ETL and dashboard."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

def get_database_url() -> str:
    return "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}".format(
        user=os.getenv("POSTGRES_USER", "eklavya"), password=os.getenv("POSTGRES_PASSWORD", "eklavya_dev_password"),
        host=os.getenv("POSTGRES_HOST", "localhost"), port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "eklavya"),
    )

def get_engine():
    return create_engine(get_database_url(), pool_pre_ping=True)
