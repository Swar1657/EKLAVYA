"""Create reproducible, structurally realistic CSV inputs for Eklavya Analytics."""
from pathlib import Path
from datetime import date, timedelta
import calendar
import numpy as np
import pandas as pd
try:
    from faker import Faker
except ImportError:  # Allows inspection-only generation when dependencies were not installed yet.
    Faker = None

np.random.seed(42)
if Faker:
    fake = Faker("en_IN")
    Faker.seed(42)
else:
    class _FallbackFaker:
        def last_name(self): return str(np.random.choice(["Patil", "Shinde", "Jadhav", "Deshmukh", "Pawar", "Kulkarni"]))
        def company(self): return f"{self.last_name()} Agro"
        def date_between(self, start_date, end_date): return date(2022, 4, 1) + timedelta(days=int(np.random.randint(0, 700)))
    fake = _FallbackFaker()
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data"
REGIONS = ["Pune", "Solapur", "Kolhapur", "Nashik", "Ahmednagar", "Sangli", "Satara", "Aurangabad"]
REGION_COUNTS = [16, 7, 8, 13, 8, 6, 6, 6]  # concentration follows major dealer markets
CROPS = ["Sugarcane", "Cotton", "Soybean", "Onion", "Banana", "Pomegranate", "Grapes", "Poly-house crops", "Ginger", "Turmeric"]

# Maharashtra crop windows derived from commonly used Kharif/Rabi planting cycles.  Peak is the
# product-application purchase month; sugarcane's principal adsali window is used in the one-row schema.
CALENDAR = {
 "Sugarcane": (7, 7), "Cotton": (6, 6), "Soybean": (6, 6), "Onion": (10, 10), "Banana": (6, 7),
 "Pomegranate": (6, 6), "Grapes": (6, 7), "Poly-house crops": (8, 8), "Ginger": (5, 5), "Turmeric": (5, 5)
}

def write(name, rows):
    pd.DataFrame(rows).to_csv(OUT / f"{name}.csv", index=False)

def peak_weight(order_day, peak_month):
    """Purchase spikes in the 4–6 weeks before peak application demand, then reverts to baseline."""
    peak = date(order_day.year, peak_month, 1)
    candidates = [peak.replace(year=peak.year - 1), peak, peak.replace(year=peak.year + 1)]
    days = min((p - order_day).days for p in candidates)
    return 6.0 if 0 <= days <= 45 else (2.2 if -15 <= days < 0 else 0.45)

def main():
    OUT.mkdir(exist_ok=True)
    today = date.today()
    end = date(today.year, today.month, 1) - timedelta(days=1)
    start = (pd.Timestamp(end) - pd.DateOffset(months=15) + pd.Timedelta(days=1)).date()
    dealers, did = [], 1
    for region, count in zip(REGIONS, REGION_COUNTS):
        for i in range(count):
            dtype = "Distributor" if np.random.random() < .70 else "Retailer"
            dealers.append(dict(dealer_id=did, dealer_name=f"{fake.last_name()} {('Agro Distributors' if dtype=='Distributor' else 'Krishi Seva Kendra')}", dealer_type=dtype, region=region, district=region, credit_limit=round(np.random.uniform(250000, 900000) if dtype == "Distributor" else np.random.uniform(60000, 250000),2), onboarding_date=fake.date_between(start_date="-5y", end_date=start)))
            did += 1
    suppliers = [dict(supplier_id=i+1, supplier_name=f"{fake.company()} Chemicals", region=REGIONS[i], lead_time_days=int(np.random.randint(7, 31))) for i in range(8)]
    materials = [dict(material_id=i+1, material_name=f"Active/Carrier Material {i+1}", supplier_id=(i%8)+1, unit_cost=round(np.random.uniform(90, 900),2), current_stock=round(np.random.uniform(500,5000),2)) for i in range(15)]
    cats = ["PGR"]*16 + ["Biostimulant"]*16 + ["Micronutrient"]*13
    packs = ["100 ml", "250 ml", "500 ml", "1 L", "250 g", "500 g", "1 kg"]
    products=[]
    for i, cat in enumerate(cats, 1):
        crop=CROPS[(i-1) % len(CROPS)]; pack=packs[(i-1)%len(packs)]; price=round(np.random.uniform(150,2500),2)
        products.append(dict(product_id=i, product_name=f"Eklavya {crop} {cat} {i:02d}", category=cat, target_crop=crop, pack_size=pack, mrp=price, dealer_price=round(price*np.random.uniform(.70,.84),2), shelf_life_months=int(np.random.choice([18,24,36]))))
    crop_calendar=[dict(crop=c, region=r, sowing_month=CALENDAR[c][0], peak_demand_month=CALENDAR[c][1]) for c in CROPS for r in REGIONS]
    batches=[]; inventory=[]; bid=iid=1
    low_products=set(np.random.choice(range(1,46), size=6, replace=False))
    for p in products:
        for b in range(np.random.randint(2,5)):
            mfg=end-timedelta(days=int(np.random.randint(20,500))); expiry=mfg+pd.DateOffset(months=p["shelf_life_months"])
            qty=round(np.random.uniform(300,1800),2); reorder=round(np.random.uniform(250,600),2)
            # Make the whole SKU low, rather than one batch low, because the dashboard aggregates batches.
            if p["product_id"] in low_products: qty=round(reorder*np.random.uniform(.12,.28),2)
            batches.append(dict(batch_id=bid,product_id=p["product_id"],production_date=mfg,quantity_produced=qty*1.5,qc_status="Passed"))
            inventory.append(dict(inventory_id=iid,product_id=p["product_id"],batch_no=f"EK-{p['product_id']:02d}-{bid:03d}",mfg_date=mfg,expiry_date=expiry.date(),quantity_available=qty,reorder_level=reorder)); bid+=1;iid+=1
    # Weighted daily candidate selection makes crop demand visibly cluster before regional peak windows.
    days=pd.date_range(start,end,freq="D").date; orders=[]; payments=[]; oid=pid=1
    for _ in range(5000):
        dealer=dealers[np.random.randint(len(dealers))]; day=days[np.random.randint(len(days))]
        weights=np.array([peak_weight(day, CALENDAR[p["target_crop"]][1]) for p in products]); product=products[np.random.choice(len(products),p=weights/weights.sum())]
        q=int(np.random.randint(5,28)); discount=round(float(np.random.choice([0,2,3,5,7],p=[.30,.25,.20,.18,.07])),2)
        total=round(q*product["dealer_price"]*(1-discount/100),2); r=np.random.random()
        if r < .65: status="Paid"; received=total; pay_day=min(day+timedelta(days=int(np.random.randint(3,30))), end)
        elif r < .85: status="Partial"; received=round(total*np.random.uniform(.35,.75),2); pay_day=min(day+timedelta(days=int(np.random.randint(10,55))), end)
        else: status="Overdue"; received=0 if np.random.random()<.55 else round(total*np.random.uniform(.05,.35),2); pay_day=None
        orders.append(dict(order_id=oid,order_date=day,dealer_id=dealer["dealer_id"],product_id=product["product_id"],quantity=q,unit_price=product["dealer_price"],discount_pct=discount,total_amount=total,dispatch_date=day+timedelta(days=int(np.random.randint(1,5))),payment_status=status))
        if received: payments.append(dict(payment_id=pid,order_id=oid,amount_received=received,payment_date=pay_day,payment_mode=np.random.choice(["NEFT","UPI","Cheque"])));pid+=1
        oid+=1
    write("dealers",dealers); write("products",products); write("suppliers",suppliers); write("raw_materials",materials); write("crop_calendar",crop_calendar); write("production_batches",batches); write("inventory",inventory); write("sales_orders",orders); write("payments",payments)
    print(f"Generated {len(orders)} orders and {len(payments)} payments in {OUT}")

if __name__ == "__main__": main()
