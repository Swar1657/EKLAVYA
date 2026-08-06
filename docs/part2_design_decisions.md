# Part 2 design decisions and run record

## Current verification state

On 13 August 2026, the local Docker daemon was unavailable, so the Part 1 PostgreSQL instance could not be queried and the requested live Part 2 run could not honestly be performed. This document deliberately does not invent accuracy, cluster, or centroid numbers. Once Docker is available, run `python -m src.forecasting.compare_models` and `python -m src.segmentation.dealer_rfm_clustering`; their printed real output is the run record to paste below.

## Forecasting

The comparison selects per SKU using an eight-week chronological holdout rather than a default model. Prophet receives yearly seasonality and the crop-calendar peak-distance regressor. XGBoost uses one pooled model with SKU ID, four lags, rolling mean, month and peak distance; pooling is more defensible than fitting roughly 60 observations per SKU.

## Segmentation

RFM is standardized before K-means. The script prints inertia and silhouette for every permitted k from 3 to 5 and chooses the maximum silhouette. Labels are derived from percentile-ranked actual centroids, not fixed cluster numbers.

## NL-to-SQL safety

The model is constrained to one SELECT, Python rejects non-SELECT/multiple statements and destructive keywords, a LIMIT 200 is applied, and execution requires a distinct read-only database URL with a five-second timeout. The API logs every question and generated query. Regex alone is not treated as the security boundary: the `eklavya_readonly` database role has SELECT grants only.

## Scope still manual

Email is the implemented n8n channel; WhatsApp Cloud API remains an extension because it requires a Meta Business account. The Part 1 views are ordinary views, so the refresh workflow verifies row counts rather than refreshing a materialized view; introduce a materialized-view cadence only if dashboard query volume justifies it.
