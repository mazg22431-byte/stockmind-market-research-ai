# Data & Models + Operations

The unified web app now exposes both modules explicitly in the sidebar.

## Data & Models
- Data source registry
- PostgreSQL system-of-record status
- Market/news/feature/signal counts
- Tree ML registry
- PyTorch LSTM registry
- FinBERT registry
- Production ensemble registry
- Unified ingestion → feature → model pipeline

## Operations
- Broker sandbox certification
- Order/fill state machine status
- Idempotency / duplicate protection
- Stale quote guard
- Broker ↔ PostgreSQL reconciliation
- Paper-trading gate
- Circuit breaker
- Emergency flatten
- Operational output console

Live trading remains gated by actual provider credentials, broker certification, OOS validation, paper trading, and conservative risk limits.
