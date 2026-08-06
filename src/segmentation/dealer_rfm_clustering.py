import logging
import pandas as pd
from sqlalchemy import text
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from src.db.connection import get_engine
logging.basicConfig(level=logging.INFO); log=logging.getLogger(__name__)

def label_centroids(frame):
    # Labels derive from relative RFM centroid positions, so they remain meaningful after data refreshes.
    ranks=frame[["recency","frequency","monetary"]].rank(pct=True)
    labels=[]
    for i,r in ranks.iterrows():
        labels.append("Champions" if r.recency<.40 and r.frequency>.60 and r.monetary>.60 else "At Risk" if r.recency>.65 and r.frequency<.50 else "Loyal" if r.frequency>.60 else "Potential" if r.recency<.50 else "Needs Attention")
    return labels

def main():
    engine=get_engine(); sql="""WITH latest AS (SELECT max(order_date) d FROM sales_orders) SELECT d.dealer_id,
    (SELECT d FROM latest)-MAX(s.order_date) recency,COUNT(*) FILTER (WHERE s.order_date >= (SELECT d FROM latest)-INTERVAL '12 months') frequency,
    SUM(s.total_amount) FILTER (WHERE s.order_date >= (SELECT d FROM latest)-INTERVAL '12 months') monetary FROM dealers d JOIN sales_orders s USING(dealer_id) GROUP BY d.dealer_id"""
    rfm=pd.read_sql(text(sql),engine).fillna(0); scaled=StandardScaler().fit_transform(rfm[["recency","frequency","monetary"]])
    diagnostics=[]
    for k in range(3,6): diagnostics.append((k,KMeans(n_clusters=k,random_state=42,n_init=20).fit(scaled).inertia_,silhouette_score(scaled,KMeans(n_clusters=k,random_state=42,n_init=20).fit_predict(scaled))))
    diag=pd.DataFrame(diagnostics,columns=["k","inertia","silhouette"]); print(diag.to_string(index=False)); k=int(diag.sort_values("silhouette",ascending=False).iloc[0].k) # best separation in permitted 3–5 range
    model=KMeans(n_clusters=k,random_state=42,n_init=20); rfm["cluster_id"]=model.fit_predict(scaled); centroids=rfm.groupby("cluster_id")[["recency","frequency","monetary"]].mean(); labels=dict(zip(centroids.index,label_centroids(centroids))); rfm["segment_label"]=rfm.cluster_id.map(labels)
    with engine.begin() as c: c.execute(text("CREATE TABLE IF NOT EXISTS dealer_segments (dealer_id INT PRIMARY KEY REFERENCES dealers(dealer_id),recency INT NOT NULL,frequency INT NOT NULL,monetary NUMERIC(14,2) NOT NULL,cluster_id INT NOT NULL,segment_label VARCHAR(40) NOT NULL)"));c.execute(text("TRUNCATE dealer_segments"))
    rfm.to_sql("dealer_segments",engine,if_exists="append",index=False); log.info("Selected k=%s. Centroids:\n%s",k,centroids.assign(segment_label=centroids.index.map(labels)))
if __name__=="__main__":main()
