CREATE OR REPLACE VIEW monthly_sales_summary AS
SELECT date_trunc('month', s.order_date)::date AS month, d.region, SUM(s.total_amount) AS total_revenue,
 COUNT(*) AS total_orders, AVG(s.total_amount) AS avg_order_value FROM sales_orders s JOIN dealers d USING(dealer_id) GROUP BY 1,2;
CREATE OR REPLACE VIEW dealer_scorecard AS
SELECT d.dealer_id,d.dealer_name,d.region, SUM(s.total_amount) AS total_revenue,COUNT(s.order_id) AS order_count,d.credit_limit,
 SUM(s.total_amount-COALESCE(p.amount_received,0)) AS current_outstanding,
 ROUND(100*SUM(s.total_amount-COALESCE(p.amount_received,0))/NULLIF(d.credit_limit,0),2) AS credit_utilization_pct
FROM dealers d LEFT JOIN sales_orders s USING(dealer_id) LEFT JOIN (SELECT order_id,SUM(amount_received) amount_received FROM payments GROUP BY order_id) p USING(order_id) GROUP BY d.dealer_id,d.dealer_name,d.region,d.credit_limit;
CREATE OR REPLACE VIEW dealer_aging_report AS
SELECT d.dealer_id,d.dealer_name,
 SUM(CASE WHEN CURRENT_DATE-s.order_date BETWEEN 0 AND 30 THEN s.total_amount-COALESCE(p.amount_received,0) ELSE 0 END) AS outstanding_0_30,
 SUM(CASE WHEN CURRENT_DATE-s.order_date BETWEEN 31 AND 60 THEN s.total_amount-COALESCE(p.amount_received,0) ELSE 0 END) AS outstanding_31_60,
 SUM(CASE WHEN CURRENT_DATE-s.order_date BETWEEN 61 AND 90 THEN s.total_amount-COALESCE(p.amount_received,0) ELSE 0 END) AS outstanding_61_90,
 SUM(CASE WHEN CURRENT_DATE-s.order_date > 90 THEN s.total_amount-COALESCE(p.amount_received,0) ELSE 0 END) AS outstanding_90_plus
FROM dealers d JOIN sales_orders s USING(dealer_id) LEFT JOIN (SELECT order_id,SUM(amount_received) amount_received FROM payments GROUP BY order_id) p USING(order_id) GROUP BY d.dealer_id,d.dealer_name;
CREATE OR REPLACE VIEW product_crop_performance AS
SELECT p.product_id,p.product_name,p.target_crop,SUM(s.total_amount) total_revenue,SUM(s.quantity) total_quantity_sold,
 RANK() OVER(PARTITION BY p.target_crop ORDER BY SUM(s.total_amount) DESC) rank_within_crop_category FROM products p LEFT JOIN sales_orders s USING(product_id) GROUP BY p.product_id,p.product_name,p.target_crop;
CREATE OR REPLACE VIEW inventory_status AS
SELECT p.product_id,p.product_name,SUM(i.quantity_available) quantity_available,MAX(i.reorder_level) reorder_level,
 (SUM(i.quantity_available)<MAX(i.reorder_level)) is_below_reorder,MIN(i.expiry_date-CURRENT_DATE) days_to_expiry FROM products p JOIN inventory i USING(product_id) GROUP BY p.product_id,p.product_name;
CREATE OR REPLACE VIEW regional_performance AS
SELECT d.region,SUM(s.total_amount) total_revenue,COUNT(DISTINCT d.dealer_id) dealer_count,SUM(s.total_amount)/NULLIF(COUNT(DISTINCT d.dealer_id),0) avg_revenue_per_dealer FROM dealers d JOIN sales_orders s USING(dealer_id) GROUP BY d.region;
