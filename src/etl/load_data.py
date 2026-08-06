"""Idempotently load generated CSVs into PostgreSQL and run integrity checks."""
import logging
from pathlib import Path
from sqlalchemy import text
from src.db.connection import get_engine
from src.etl.validate import validate_database

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log=logging.getLogger(__name__)
ROOT=Path(__file__).resolve().parents[2]
TABLES=["payments","sales_orders","inventory","production_batches","raw_materials","crop_calendar","dealers","products","suppliers"]
LOAD_ORDER=["dealers","products","suppliers","raw_materials","crop_calendar","production_batches","inventory","sales_orders","payments"]

def run_sql(engine,path):
    with engine.begin() as conn: conn.execute(text(path.read_text(encoding="utf-8")))

def main():
    engine=get_engine()
    log.info("Creating schema if needed")
    run_sql(engine,ROOT/"src/db/schema.sql")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE " + ", ".join(TABLES) + " RESTART IDENTITY CASCADE"))
    for table in LOAD_ORDER:
        csv=ROOT/"data"/f"{table}.csv"
        if not csv.exists(): raise FileNotFoundError(f"Missing {csv}; run the generator first.")
        import pandas as pd
        frame=pd.read_csv(csv)
        frame.to_sql(table,engine,if_exists="append",index=False,method="multi")
        log.info("Loaded %s rows into %s",len(frame),table)
    if not validate_database(engine): raise SystemExit("Validation failed; database retained for inspection.")
    log.info("ETL completed successfully")

if __name__ == "__main__": main()
