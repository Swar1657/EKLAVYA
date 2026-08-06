"""Run both holdout models and persist the actual winner per SKU/week."""
import logging
import numpy as np
import pandas as pd
from sqlalchemy import text
from src.db.connection import get_engine
from src.forecasting.prepare_timeseries import prepare_timeseries,train_test_split
from src.forecasting.prophet_forecast import forecast_product
from src.forecasting.xgboost_forecast import forecast_global
logging.basicConfig(level=logging.INFO); log=logging.getLogger(__name__)

def main():
    data=prepare_timeseries(); splits=train_test_split(data); xgb=forecast_global(data,splits); rows=[]; wins=[]; scores=[]
    for pid,(train,test) in splits.items():
        pp,pm,pr=forecast_product(train,test); xp,xm,xr=xgb[pid]; winner="Prophet" if pm<=xm else "XGBoost"; pred=pp if winner=="Prophet" else xp
        wins.append(winner); scores.extend([("Prophet",pm),("XGBoost",xm)])
        for ds,yhat,y in zip(test.ds,pred,test.y): rows.append(dict(product_id=int(pid),model_used=winner,mape=pm,rmse=pr if winner=="Prophet" else xr,forecast_month=pd.Timestamp(ds).date(),predicted_qty=float(yhat),actual_qty=float(y)))
    engine=get_engine()
    with engine.begin() as c:
        c.execute(text("""CREATE TABLE IF NOT EXISTS demand_forecast_results (product_id INT REFERENCES products(product_id),model_used VARCHAR(20) NOT NULL,mape NUMERIC(10,4) NOT NULL,rmse NUMERIC(12,4) NOT NULL,forecast_month DATE NOT NULL,predicted_qty NUMERIC(12,2) NOT NULL,actual_qty NUMERIC(12,2) NOT NULL,PRIMARY KEY(product_id,forecast_month))"""));c.execute(text("TRUNCATE demand_forecast_results"))
    pd.DataFrame(rows).to_sql("demand_forecast_results",engine,if_exists="append",index=False)
    summary=pd.DataFrame(scores,columns=["model","mape"]).groupby("model").mape.mean(); log.info("Wins: %s; overall MAPE: %s",pd.Series(wins).value_counts().to_dict(),summary.round(2).to_dict())
    print(pd.DataFrame({"wins":pd.Series(wins).value_counts(),"mean_mape":summary}))
if __name__=="__main__": main()
