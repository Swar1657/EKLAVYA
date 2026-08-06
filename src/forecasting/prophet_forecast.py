import numpy as np
from prophet import Prophet

def forecast_product(train,test):
    model=Prophet(yearly_seasonality=True,weekly_seasonality=False,daily_seasonality=False)
    model.add_regressor("days_to_peak_demand")
    model.fit(train[["ds","y","days_to_peak_demand"]])
    future=test[["ds","days_to_peak_demand"]]
    pred=model.predict(future)["yhat"].clip(lower=0).to_numpy()
    actual=test.y.to_numpy(); mape=float(np.mean(np.abs(actual-pred)/np.maximum(actual,1))*100); rmse=float(np.sqrt(np.mean((actual-pred)**2)))
    return pred,mape,rmse
