# Eklavya Sales & Inventory Analytics Platform

A synthetic, runnable analytics foundation for a Maharashtra agrochemical manufacturer. It consolidates dealer sales, product/crop demand, inventory and receivables into PostgreSQL and a Streamlit dashboard. It is deliberately Part 1 only: automation, forecasting, segmentation and NL-to-SQL are **not** included. `# TODO (Part 2):` those capabilities can build on this settled schema.

## Setup

1. Copy `.env.example` to `.env`, then run `docker-compose up -d`.
2. Create a Python 3.11 virtual environment and install `pip install -r requirements.txt`.
3. Generate inspectable input files: `python -m src.generate.generate_synthetic_data`.
4. Load and validate: `python -m src.etl.load_data`.
5. Create dashboard views: `psql -h localhost -U eklavya -d eklavya -f src/views/create_views.sql`.
6. Run checks: `pytest`.
7. Launch: `streamlit run src/dashboard/app.py`.

## Design decisions

PostgreSQL provides reliable transactions, foreign keys, numerics for rupee values and reusable views that make the dashboard's business definitions consistent. The schema keeps entities such as dealers, products, batches, orders and payments separate, preventing duplicated details and preserving traceability from a dashboard number back to a transaction.

Seasonality is encoded from Maharashtra planting/application windows, rather than added as arbitrary noise. Every sale chooses a product with a sharply higher selection weight during the 45 days before that product crop's regional peak month; all other periods retain a lower baseline. This makes anticipated crop-cycle demand clearly visible in monthly trends while still retaining normal commercial variation.

The generator has a fixed seed and writes CSVs before database loading. This lets reviewers inspect or test the exact same dataset repeatedly. The loader truncates and reloads in dependency order, so reruns are safe.
