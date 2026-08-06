# Data dictionary

| Table | Column | Type | Meaning |
|---|---|---|---|
| dealers | dealer_id | serial | Unique dealer key. |
| dealers | dealer_name, dealer_type, region, district | varchar | Dealer identity, channel and geography. |
| dealers | credit_limit | numeric | Approved outstanding-credit ceiling. |
| dealers | onboarding_date | date | Date dealer relationship began. |
| products | product_id | serial | Unique SKU key. |
| products | product_name, category, target_crop, pack_size | varchar | Commercial SKU attributes. |
| products | mrp, dealer_price | numeric | Pack retail and dealer prices. |
| products | shelf_life_months | int | Approved shelf life. |
| suppliers | supplier_id | serial | Unique supplier key. |
| suppliers | supplier_name, region | varchar | Supplier identity and location. |
| suppliers | lead_time_days | int | Typical procurement lead time. |
| raw_materials | material_id | serial | Unique material key. |
| raw_materials | material_name | varchar | Material description. |
| raw_materials | supplier_id | int | Supplying supplier. |
| raw_materials | unit_cost, current_stock | numeric | Unit cost and stock balance. |
| crop_calendar | crop, region | varchar | Crop-region composite key. |
| crop_calendar | sowing_month, peak_demand_month | int | Seasonal planting and input-demand months. |
| production_batches | batch_id | serial | Production batch key. |
| production_batches | product_id, production_date, quantity_produced, qc_status | int/date/numeric/varchar | Batch SKU, date, output and quality state. |
| inventory | inventory_id | serial | Inventory batch key. |
| inventory | product_id, batch_no | int/varchar | SKU and traceable batch number. |
| inventory | mfg_date, expiry_date | date | Manufacturing and expiry dates. |
| inventory | quantity_available, reorder_level | numeric | Available batch stock and replenishment threshold. |
| sales_orders | order_id | serial | Sales transaction key. |
| sales_orders | order_date, dealer_id, product_id | date/int | Order date and transaction relationships. |
| sales_orders | quantity, unit_price, discount_pct, total_amount | int/numeric | Ordered packs and final invoice value. |
| sales_orders | dispatch_date, payment_status | date/varchar | Fulfilment date and receivable state. |
| payments | payment_id | serial | Payment record key. |
| payments | order_id, amount_received, payment_date, payment_mode | int/numeric/date/varchar | Applied order receipt details. |
