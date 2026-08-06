import math
import pandas as pd
import pytest
from src.forecasting.prepare_timeseries import prepare_timeseries, train_test_split

pytest.importorskip("sqlalchemy")

def test_prepare_timeseries_returns_dataframe_and_split(monkeypatch):
    rows = []
    for product_id in [101, 102]:
        for offset in range(20):
            ds = pd.Timestamp("2023-01-01") + pd.Timedelta(weeks=offset)
            rows.append({
                "product_id": product_id,
                "ds": ds.date(),
                "y": float(offset + 1),
                "peak_month": 3,
            })

    monkeypatch.setattr("src.forecasting.prepare_timeseries.get_engine", lambda: object())
    monkeypatch.setattr("src.forecasting.prepare_timeseries.pd.read_sql", lambda *args, **kwargs: pd.DataFrame(rows))

    data = prepare_timeseries(top_n=2)
    assert isinstance(data, pd.DataFrame)
    assert {"product_id", "ds", "y", "days_to_peak_demand"}.issubset(data.columns)

    splits = train_test_split(data)
    assert isinstance(splits, dict)
    assert set(splits) == {101, 102}
    for pid, (train, test) in splits.items():
        assert len(test) == 8
        assert len(train) == len(data[data.product_id == pid]) - 8
        assert set(train.columns) == set(test.columns)


def test_forecast_results_if_database_available():
    from src.db.connection import get_engine
    from sqlalchemy import text
    try:
        with get_engine().connect() as c: rows=c.execute(text("SELECT predicted_qty,mape FROM demand_forecast_results")).all()
    except Exception: pytest.skip("Postgres forecast results are not available")
    assert len(rows) >= 80 and all(float(r[0])>=0 and math.isfinite(float(r[1])) for r in rows)
