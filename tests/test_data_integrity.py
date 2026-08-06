from pathlib import Path
import pandas as pd

DATA=Path(__file__).resolve().parents[1]/"data"
def read(name): return pd.read_csv(DATA/f"{name}.csv")

def test_expected_row_counts():
    assert len(read("dealers")) == 70
    assert len(read("products")) == 45
    assert 4000 <= len(read("sales_orders")) <= 6000

def test_no_orphan_foreign_keys():
    assert set(read("sales_orders").dealer_id).issubset(set(read("dealers").dealer_id))
    assert set(read("sales_orders").product_id).issubset(set(read("products").product_id))
    assert set(read("payments").order_id).issubset(set(read("sales_orders").order_id))

def test_non_negative_amounts_and_quantities():
    for frame, cols in [(read("sales_orders"),["quantity","unit_price","total_amount"]),(read("inventory"),["quantity_available","reorder_level"]),(read("payments"),["amount_received"])]: assert (frame[cols] >= 0).all().all()

def test_payment_status_matches_received_sum():
    orders=read("sales_orders"); sums=read("payments").groupby("order_id").amount_received.sum(); received=orders.order_id.map(sums).fillna(0)
    assert (received[orders.payment_status == "Paid"].round(2) == orders.loc[orders.payment_status == "Paid","total_amount"].round(2)).all()
    assert (received[orders.payment_status != "Paid"] < orders.loc[orders.payment_status != "Paid","total_amount"]).all()

def test_low_stock_and_old_overdue_exist():
    inv=read("inventory").groupby("product_id").agg(quantity_available=("quantity_available","sum"),reorder_level=("reorder_level","max"))
    assert (inv.quantity_available < inv.reorder_level).any()
    orders=read("sales_orders"); assert ((orders.payment_status == "Overdue") & (pd.to_datetime(orders.order_date) < pd.Timestamp.today()-pd.Timedelta(days=90))).any()
