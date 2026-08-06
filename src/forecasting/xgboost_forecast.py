import numpy as np
import pandas as pd
from xgboost import XGBRegressor

def features(frame):
    x=frame.copy().sort_values(["product_id","ds"])
    x["product_id"]=pd.to_numeric(x["product_id"],errors="raise").astype(int)
    x["y"]=pd.to_numeric(x["y"],errors="coerce").fillna(0.0)
    x["days_to_peak_demand"]=pd.to_numeric(x["days_to_peak_demand"],errors="coerce").fillna(0.0)
    for i in range(1,5): x[f"lag_{i}"]=pd.to_numeric(x.groupby("product_id").y.shift(i),errors="coerce")
    x["rolling_4"]=pd.to_numeric(x.groupby("product_id").y.transform(lambda s:s.shift(1).rolling(4).mean()),errors="coerce")
    x["month"]=pd.to_numeric(x.ds.dt.month,errors="coerce").astype(float)
    return x

def forecast_global(data,splits):
    # A global model pools signal across SKUs; separate ~60-week models would overfit sparse histories.
    train_end=max(t.ds.max() for t,_ in splits.values()); train=features(data[data.ds<=train_end]).dropna()
    cols=["lag_1","lag_2","lag_3","lag_4","rolling_4","month","days_to_peak_demand"]
    train[cols]=train[cols].apply(pd.to_numeric,errors="coerce")
    model=XGBRegressor(n_estimators=180,max_depth=3,learning_rate=.05,objective="reg:squarederror",random_state=42)
    model.fit(train[cols],train.y); results={}
    for pid,(hist,test) in splits.items():
        working=pd.concat([hist,test.assign(y=np.nan)]).copy(); preds=[]
        for idx in working.index[-len(test):]:
            row=features(working.loc[:idx].fillna({"y":0})).loc[idx,cols].apply(pd.to_numeric,errors="coerce").to_frame().T.astype(float)
            yhat=max(0,float(model.predict(row)[0])); working.loc[idx,"y"]=yhat; preds.append(yhat)
        actual=test.y.to_numpy(); pred=np.array(preds); results[pid]=(pred,float(np.mean(np.abs(actual-pred)/np.maximum(actual,1))*100),float(np.sqrt(np.mean((actual-pred)**2))))
    return results
