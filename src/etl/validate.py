"""Validation rules for the synthetic transactional model."""
import logging
from sqlalchemy import text

log = logging.getLogger(__name__)

def validate_database(engine) -> bool:
    checks = {
      "No null required relationship keys": """SELECT COUNT(*) FROM sales_orders WHERE dealer_id IS NULL OR product_id IS NULL
          UNION ALL SELECT COUNT(*) FROM payments WHERE order_id IS NULL""",
      "No orphan foreign keys": """SELECT COUNT(*) FROM sales_orders s LEFT JOIN dealers d ON s.dealer_id=d.dealer_id LEFT JOIN products p ON s.product_id=p.product_id WHERE d.dealer_id IS NULL OR p.product_id IS NULL
          UNION ALL SELECT COUNT(*) FROM payments x LEFT JOIN sales_orders s ON x.order_id=s.order_id WHERE s.order_id IS NULL""",
      "No negative prices or quantities": """SELECT COUNT(*) FROM sales_orders WHERE quantity < 0 OR unit_price < 0 OR total_amount < 0
          UNION ALL SELECT COUNT(*) FROM inventory WHERE quantity_available < 0 OR reorder_level < 0""",
      # Paid must reconcile exactly; partial/overdue must remain below the invoiced total.
      "Payment status reconciles to received amounts": """SELECT COUNT(*) FROM sales_orders s LEFT JOIN (SELECT order_id, SUM(amount_received) amount FROM payments GROUP BY order_id) p ON p.order_id=s.order_id
          WHERE (s.payment_status='Paid' AND COALESCE(p.amount,0) <> s.total_amount)
             OR (s.payment_status IN ('Partial','Overdue') AND COALESCE(p.amount,0) >= s.total_amount)""",
    }
    passed=True
    with engine.connect() as conn:
        for label, sql in checks.items():
            failures=sum(row[0] for row in conn.execute(text(sql)).all())
            if failures: log.error("FAIL: %s (%s rows)", label, failures); passed=False
            else: log.info("PASS: %s", label)
    return passed
