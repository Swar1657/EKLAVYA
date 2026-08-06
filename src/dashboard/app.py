import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import text
from src.db.connection import get_engine

st.set_page_config(page_title="Eklavya Analytics", layout="wide")
st.title("Eklavya Sales & Inventory Analytics Platform")

@st.cache_data(ttl=300)
def query(sql):
    return pd.read_sql(text(sql), get_engine())

regions=query("SELECT DISTINCT region FROM dealers ORDER BY region")["region"].tolist()
minmax=query("SELECT MIN(order_date) lo, MAX(order_date) hi FROM sales_orders").iloc[0]
with st.sidebar:
    st.header("Global filters")
    selected_regions=st.multiselect("Region",regions,default=regions)
    dates=st.date_input("Order date range",value=(minmax.lo,minmax.hi),min_value=minmax.lo,max_value=minmax.hi)

def where(alias="d"):
    quoted=", ".join("'"+r.replace("'", "''")+"'" for r in selected_regions) or "''"
    return f"{alias}.region IN ({quoted}) AND s.order_date BETWEEN '{dates[0]}' AND '{dates[-1]}'"

tabs=st.tabs(["Executive Summary","Dealer Performance","Product & Crop Analysis","Inventory","Payments & Aging","Forecast","Dealer Segments","Ask a Question"])
with tabs[0]:
    k=query(f"SELECT COALESCE(SUM(s.total_amount),0) revenue, COUNT(*) orders, COUNT(DISTINCT s.dealer_id) dealers, COALESCE(AVG(s.total_amount),0) aov FROM sales_orders s JOIN dealers d USING(dealer_id) WHERE {where()}").iloc[0]
    cols=st.columns(4); cols[0].metric("Total revenue",f"₹{k.revenue:,.0f}");cols[1].metric("Total orders",f"{k.orders:,}");cols[2].metric("Active dealers",k.dealers);cols[3].metric("Average order value",f"₹{k.aov:,.0f}")
    monthly=query(f"SELECT date_trunc('month',s.order_date)::date AS month_start,SUM(s.total_amount) AS revenue FROM sales_orders s JOIN dealers d USING(dealer_id) WHERE {where()} GROUP BY 1 ORDER BY 1")
    st.plotly_chart(px.line(monthly,x="month_start",y="revenue",markers=True,title="Monthly revenue"),use_container_width=True)
    c1,c2=st.columns(2); regional=query(f"SELECT d.region,SUM(s.total_amount) revenue FROM sales_orders s JOIN dealers d USING(dealer_id) WHERE {where()} GROUP BY 1 ORDER BY 2 DESC LIMIT 5"); dealers=query(f"SELECT d.dealer_name,SUM(s.total_amount) revenue FROM sales_orders s JOIN dealers d USING(dealer_id) WHERE {where()} GROUP BY 1 ORDER BY 2 DESC LIMIT 5")
    c1.plotly_chart(px.bar(regional,x="region",y="revenue",title="Top regions"),use_container_width=True);c2.dataframe(dealers,hide_index=True,use_container_width=True)
with tabs[1]:
    score=query("SELECT sc.*,d.dealer_type FROM dealer_scorecard sc JOIN dealers d USING(dealer_id)")
    types=st.multiselect("Dealer type",score.dealer_type.unique(),default=score.dealer_type.unique())
    score=score[score.region.isin(selected_regions)&score.dealer_type.isin(types)].sort_values("total_revenue",ascending=False)
    st.dataframe(score,hide_index=True,use_container_width=True); st.plotly_chart(px.scatter(score,x="credit_utilization_pct",y="total_revenue",hover_name="dealer_name",color="region",title="Credit exposure vs revenue"),use_container_width=True)
with tabs[2]:
    perf=query(f"SELECT p.product_name,p.target_crop,SUM(s.total_amount) revenue FROM sales_orders s JOIN products p USING(product_id) JOIN dealers d USING(dealer_id) WHERE {where()} GROUP BY 1,2")
    c1,c2=st.columns(2);c1.plotly_chart(px.bar(perf.nlargest(10,"revenue"),x="revenue",y="product_name",orientation="h",title="Top 10 SKUs"),use_container_width=True);c2.plotly_chart(px.bar(perf.nsmallest(10,"revenue"),x="revenue",y="product_name",orientation="h",title="Bottom 10 SKUs"),use_container_width=True)
    crop=st.selectbox("Target crop",sorted(perf.target_crop.unique())); curve=query(f"SELECT date_trunc('month',s.order_date)::date AS month_start,SUM(s.quantity) AS quantity FROM sales_orders s JOIN products p USING(product_id) JOIN dealers d USING(dealer_id) WHERE {where()} AND p.target_crop='{crop}' GROUP BY 1 ORDER BY 1")
    peak=query(f"SELECT peak_demand_month FROM crop_calendar WHERE crop='{crop}' LIMIT 1").iloc[0,0];st.plotly_chart(px.line(curve,x="month_start",y="quantity",markers=True,title=f"{crop} demand curve — peak purchase month: {peak}"),use_container_width=True)
with tabs[3]:
    inv=query("SELECT * FROM inventory_status ORDER BY is_below_reorder DESC, days_to_expiry ASC"); st.subheader("Below reorder level");st.dataframe(inv[inv.is_below_reorder],hide_index=True,use_container_width=True)
    expiry=query("SELECT p.product_name,i.batch_no,i.expiry_date,i.quantity_available,(i.expiry_date-CURRENT_DATE) days_to_expiry FROM inventory i JOIN products p USING(product_id) WHERE i.expiry_date-CURRENT_DATE BETWEEN 0 AND 60 ORDER BY i.expiry_date");st.subheader("Near expiry (60 days)");st.dataframe(expiry,hide_index=True,use_container_width=True)
with tabs[4]:
    aging=query("SELECT * FROM dealer_aging_report"); buckets=aging[["outstanding_0_30","outstanding_31_60","outstanding_61_90","outstanding_90_plus"]].sum().rename_axis("bucket").reset_index(name="outstanding");st.plotly_chart(px.bar(buckets,x="bucket",y="outstanding",title="Outstanding aging"),use_container_width=True)
    term=st.text_input("Search dealer"); st.dataframe(aging[aging.dealer_name.str.contains(term,case=False,na=False)],hide_index=True,use_container_width=True)
with tabs[5]:
    st.subheader("Eight-week holdout demand forecast")
    try:
        forecasts=query("SELECT f.*,p.product_name FROM demand_forecast_results f JOIN products p USING(product_id) ORDER BY forecast_month")
        st.dataframe(forecasts,hide_index=True,use_container_width=True)
        st.plotly_chart(px.line(forecasts,x="forecast_month",y=["actual_qty","predicted_qty"],color="product_name",title="Actual vs selected-model forecast"),use_container_width=True)
    except Exception: st.info("Run `python -m src.forecasting.compare_models` after Postgres is available to populate forecasts.")
with tabs[6]:
    st.subheader("RFM dealer segments")
    try:
        segments=query("SELECT s.*,d.dealer_name FROM dealer_segments s JOIN dealers d USING(dealer_id)")
        st.dataframe(segments,hide_index=True,use_container_width=True)
        st.plotly_chart(px.scatter(segments,x="frequency",y="monetary",size="recency",color="segment_label",hover_name="dealer_name"),use_container_width=True)
    except Exception: st.info("Run `python -m src.segmentation.dealer_rfm_clustering` after Postgres is available.")
with tabs[7]:
    st.subheader("Ask a Question")
    question=st.text_input("Ask about sales, stock, receivables, forecasts, or segments")
    if question:
        import requests
        try:
            answer=requests.post("http://localhost:8000/query",json={"question":question},timeout=10).json()
            st.write(answer.get("summary"));st.code(answer.get("sql",""));st.dataframe(pd.DataFrame(answer.get("results",[])),hide_index=True)
        except Exception: st.warning("Start the read-only API with `uvicorn src.nl_query.api:app --reload` and configure its credentials.")
