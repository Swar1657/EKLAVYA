import os,re
import pandas as pd
from sqlalchemy import create_engine,text
from groq import Groq
from src.nl_query.schema_context import SCHEMA_CONTEXT
FORBIDDEN=re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|GRANT|REVOKE)\b",re.I)
def validate_sql(sql):
    clean=sql.strip().rstrip(";")
    if not clean.upper().startswith("SELECT") or FORBIDDEN.search(clean) or ";" in clean: raise ValueError("Only one safe SELECT statement is permitted.")
    return clean if re.search(r"\bLIMIT\s+\d+\b",clean,re.I) else clean+" LIMIT 200"
def generate_sql(question):
    client=Groq(api_key=os.environ["GROQ_API_KEY"])
    prompt=f"{SCHEMA_CONTEXT}\nReturn ONLY one PostgreSQL SELECT for: {question}. Never modify data."
    return validate_sql(client.chat.completions.create(model=os.getenv("GROQ_MODEL","llama-3.1-8b-instant"),messages=[{"role":"system","content":prompt}]).choices[0].message.content)
def readonly_engine():
    url=os.getenv("READONLY_DATABASE_URL")
    if not url: raise RuntimeError("READONLY_DATABASE_URL must use eklavya_readonly; refusing to execute with owner credentials.")
    return create_engine(url,connect_args={"options":"-c statement_timeout=5000"})
def execute_safe(sql): return pd.read_sql(text(validate_sql(sql)),readonly_engine()).head(200)
def summarize(question,results):
    if results.empty:return "No matching records were found."
    client=Groq(api_key=os.environ["GROQ_API_KEY"]); message=f"Question: {question}\nRows: {results.head(20).to_json(orient='records')}\nSummarize in 1-2 plain sentences."
    return client.chat.completions.create(model=os.getenv("GROQ_MODEL","llama-3.1-8b-instant"),messages=[{"role":"user","content":message}]).choices[0].message.content
