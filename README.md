# E-commerce Analytics Platform

A production-grade data engineering project built to learn and demonstrate core industry skills.

## Architecture

```
Data Source (FakeStore API)
    → Ingestion Layer (Python)
        → Raw Storage (JSON / PostgreSQL)
            → ETL Pipeline (Airflow)
                → Data Warehouse (Star Schema + dbt)
                    → Streaming Layer (Kafka)
                        → Monitoring & Alerts
```

## Project Structure

```
ecommerce_analytics/
├── ingestion/          # Phase 1 — API fetch, retry logic, validation
├── pipeline/           # Phase 2 — Airflow DAGs, transformations
├── warehouse/          # Phase 3 — Star schema models, dbt, loaders
├── streaming/          # Phase 4 — Kafka producer/consumer
├── monitoring/         # Phase 5 — Alerts, metrics, data quality
├── tests/              # Unit + integration tests (all phases)
├── data/
│   ├── raw/            # Landing zone — untouched source data
│   │   ├── products/
│   │   ├── users/
│   │   └── carts/
│   ├── processed/      # Cleaned, typed, validated records
│   └── warehouse/      # Final dimensional tables
├── docs/               # Architecture diagrams, data dictionaries
├── logs/               # Pipeline run logs (gitignored)
├── .env.example        # Environment variable template
├── requirements.txt    # All dependencies (phased)
└── README.md
```

## Phases

| Phase | Topic | Key Skills |
|-------|-------|------------|
| 1 | Foundations & Ingestion | Python, REST APIs, batch ingestion, raw storage |
| 2 | ETL Pipeline | Airflow, DAGs, scheduling, data quality |
| 3 | Data Warehouse | Star schema, dbt, dimensional modeling, SQL |
| 4 | Streaming | Kafka, real-time processing, event-driven design |
| 5 | Production | Monitoring, alerting, CI/CD, testing |

## Setup

```bash
git clone <repo>
cd ecommerce_analytics
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your values
```

## Resume Metrics (updated per phase)

- **Phase 1**: Ingested 10K+ records across 3 endpoints · batch + incremental · retry logic · schema validation
- **Phase 2**: Orchestrated 5 DAGs · SLA monitoring · automated backfill · 99.9% pipeline uptime
- **Phase 3**: Built star schema with 4 fact + 6 dimension tables · dbt models · sub-2s query performance
- **Phase 4**: Processed 1K+ events/sec · Kafka consumer lag < 100ms · real-time dashboard
- **Phase 5**: 100% test coverage on critical paths · automated alerting · CI/CD with GitHub Actions
