"""Shared weekly SKU time-series preparation; no random/shuffled split is used."""
import pandas as pd
from sqlalchemy import text
from src.db.connection import get_engine

def prepare_timeseries(top_n=12):
    engine=get_engine()
    sql="""WITH top_skus AS (SELECT product_id FROM product_crop_performance ORDER BY total_revenue DESC LIMIT :n)
    SELECT s.product_id, date_trunc('week',s.order_date)::date AS ds, SUM(s.quantity)::float AS y,
           MIN(c.peak_demand_month) AS peak_month
    FROM sales_orders s JOIN products p USING(product_id) JOIN crop_calendar c ON c.crop=p.target_crop
    WHERE s.product_id IN (SELECT product_id FROM top_skus)
    GROUP BY s.product_id, date_trunc('week',s.order_date) ORDER BY product_id,ds"""
    data=pd.read_sql(text(sql),engine,params={"n":top_n}); data["ds"]=pd.to_datetime(data["ds"])
    data["product_id"]=pd.to_numeric(data["product_id"],errors="raise").astype(int)
    data["y"]=pd.to_numeric(data["y"],errors="coerce").fillna(0.0)
    data["peak_month"]=pd.to_numeric(data["peak_month"],errors="coerce")
    # Signed distance to the closest occurrence of that crop's peak-demand month.
    def distance(row):
        anchors=[pd.Timestamp(year=y,month=int(row.peak_month),day=1) for y in (row.ds.year-1,row.ds.year,row.ds.year+1)]
        return min(((a-row.ds).days for a in anchors),key=abs)
    data["days_to_peak_demand"]=data.apply(distance,axis=1).astype(float)
    # Explicitly materialise missing weeks as zeros, because no order means zero demand, not absent data.
    out=[]
    for product_id,g in data.groupby("product_id"):
        g=g.set_index("ds").asfreq("W-MON").fillna({"y":0,"product_id":product_id,"peak_month":g.peak_month.iloc[0]})
        g["days_to_peak_demand"]=[distance(r) for _,r in g.reset_index().iterrows()]; out.append(g.reset_index())
    data=pd.concat(out,ignore_index=True)
    return data


def train_test_split(data):
    return {pid:(g.iloc[:-8].copy(),g.iloc[-8:].copy()) for pid,g in data.groupby("product_id")}
