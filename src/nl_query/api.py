import logging
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from src.nl_query.nl_to_sql import generate_sql,execute_safe,summarize
logging.basicConfig(filename="nl_query_audit.log",level=logging.INFO,format="%(asctime)s %(message)s")
app=FastAPI(title="Eklavya Read-only NL Query API")
class Question(BaseModel): question:str
@app.post("/query")
def query(body:Question):
    try:
        sql=generate_sql(body.question); logging.info("question=%r sql=%r",body.question,sql); result=execute_safe(sql)
        return {"sql":sql,"results":result.to_dict(orient="records"),"summary":summarize(body.question,result)}
    except (ValueError,RuntimeError) as e: raise HTTPException(400,str(e))
    except Exception as e: logging.exception("NL query failed"); raise HTTPException(500,"Query service could not complete the request.") from e
