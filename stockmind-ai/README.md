# StockMind AI IDX — Unified v1→v7

This repository is the consolidated application built from the supplied StockMind v1, v2, v3, v4, v5, v6 and v7 archives.

## Included

- Initial web dashboard and stock analysis
- PostgreSQL + SQLModel persistence
- Redis + Celery job queue
- Authentication
- Licensed IDX data adapter
- Security master and delisted-stock controls
- Corporate actions and adjusted-price pipeline
- Feature store
- Tree-based ML
- PyTorch LSTM
- FinBERT sentiment
- ML + LSTM + FinBERT ensemble
- Model registry
- No-code rules strategy builder
- Walk-forward / leakage-aware validation
- Realistic backtesting with commission/slippage/sizing/SL/TP
- Portfolio risk controls
- Paper-trading gate
- Broker sandbox certification harness
- Order/fill state machine
- Idempotent client order IDs
- Broker/PostgreSQL reconciliation
- Stale-quote detection
- Circuit breaker and emergency flatten
- Monitoring/ops controls
- Vault/KMS-compatible secret injection
- Unified web UI from dashboard to operations

## Start

1. Copy `backend/.env.example` to `backend/.env`.
2. Configure PostgreSQL/Redis.
3. Configure the licensed IDX market-data provider.
4. Configure the licensed news provider.
5. Configure the official exchange calendar.
6. Configure broker sandbox credentials.
7. Run:

```bash
docker compose up --build
```

Open the frontend with a static server or through the deployment's web server. The API defaults to port 8000.

## Important

The software does not invent market data, licenses, credentials, broker certification, or validation results. Those are external dependencies that must be supplied and verified before live capital is enabled.


## StockMind Market Research extensions

- AI Breaking News: IDX ticker search, real-time/near-real-time news retrieval through the configured news provider or Google News RSS fallback, hype ranking, sentiment scoring, source links, and five daily AI-ranked posts.
- AI Bandar Detector: Broker Summary, Broker Distribution, Broker Flow, Trade Flow and Fundachart layout with a provider-ready adapter.
- Screener Preset: Bandarmology, Technical and Fundamental presets in one page.
- Astro Market Method (experimental): five-stage workflow — Financial, Fibonacci Time, Technical, Fundamental and Bandarmology — with analysis date and score table.
- Dedicated top toolbar above the IDX / AI Market Signal header.
- Full-color 3D-style icon system and the supplied StockMind Market Research logo.

The UI includes demo fallbacks so the workspace remains inspectable without backend credentials. Demo broker-flow figures are explicitly labeled and should be replaced with a verified broker-data feed before production use. The Astro module is presented as an experimental heuristic, not a scientifically validated predictive method.

For a true daily auto-post schedule, run the Celery task `stockmind.app.tasks.daily_breaking_news` from Celery Beat (or your production scheduler) once per day. The task caches the five selected posts for 24 hours.

## Astrology Deep Dive

See `ASTROLOGY_PROVIDER_SETUP.md` for the ephemeris provider architecture, Swiss Ephemeris licensing notes, and environment variables for the Astro Market Deep Dive module.
