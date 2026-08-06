CREATE TABLE IF NOT EXISTS dealers (
    dealer_id SERIAL PRIMARY KEY, dealer_name VARCHAR(120) NOT NULL,
    dealer_type VARCHAR(20) NOT NULL CHECK (dealer_type IN ('Distributor','Retailer')),
    region VARCHAR(60) NOT NULL, district VARCHAR(60) NOT NULL,
    credit_limit NUMERIC(12,2) NOT NULL, onboarding_date DATE NOT NULL
);
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY, product_name VARCHAR(120) NOT NULL, category VARCHAR(60) NOT NULL,
    target_crop VARCHAR(60) NOT NULL, pack_size VARCHAR(30) NOT NULL, mrp NUMERIC(10,2) NOT NULL,
    dealer_price NUMERIC(10,2) NOT NULL, shelf_life_months INT NOT NULL
);
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id SERIAL PRIMARY KEY, supplier_name VARCHAR(120) NOT NULL, region VARCHAR(60) NOT NULL, lead_time_days INT NOT NULL
);
CREATE TABLE IF NOT EXISTS raw_materials (
    material_id SERIAL PRIMARY KEY, material_name VARCHAR(120) NOT NULL,
    supplier_id INT REFERENCES suppliers(supplier_id), unit_cost NUMERIC(10,2) NOT NULL, current_stock NUMERIC(12,2) NOT NULL
);
CREATE TABLE IF NOT EXISTS crop_calendar (
    crop VARCHAR(60) NOT NULL, region VARCHAR(60) NOT NULL,
    sowing_month INT NOT NULL CHECK (sowing_month BETWEEN 1 AND 12),
    peak_demand_month INT NOT NULL CHECK (peak_demand_month BETWEEN 1 AND 12), PRIMARY KEY (crop, region)
);
CREATE TABLE IF NOT EXISTS production_batches (
    batch_id SERIAL PRIMARY KEY, product_id INT REFERENCES products(product_id), production_date DATE NOT NULL,
    quantity_produced NUMERIC(12,2) NOT NULL, qc_status VARCHAR(20) NOT NULL CHECK (qc_status IN ('Passed','Failed','Pending'))
);
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id SERIAL PRIMARY KEY, product_id INT REFERENCES products(product_id), batch_no VARCHAR(30) NOT NULL,
    mfg_date DATE NOT NULL, expiry_date DATE NOT NULL, quantity_available NUMERIC(12,2) NOT NULL, reorder_level NUMERIC(12,2) NOT NULL
);
CREATE TABLE IF NOT EXISTS sales_orders (
    order_id SERIAL PRIMARY KEY, order_date DATE NOT NULL, dealer_id INT REFERENCES dealers(dealer_id), product_id INT REFERENCES products(product_id),
    quantity INT NOT NULL, unit_price NUMERIC(10,2) NOT NULL, discount_pct NUMERIC(5,2) NOT NULL DEFAULT 0,
    total_amount NUMERIC(12,2) NOT NULL, dispatch_date DATE, payment_status VARCHAR(20) NOT NULL CHECK (payment_status IN ('Paid','Partial','Overdue'))
);
CREATE TABLE IF NOT EXISTS payments (
    payment_id SERIAL PRIMARY KEY, order_id INT REFERENCES sales_orders(order_id), amount_received NUMERIC(12,2) NOT NULL,
    payment_date DATE NOT NULL, payment_mode VARCHAR(20) 
);
