# Unified architecture

All versions are now one deployable application.

```text
Licensed IDX + licensed news + official calendar + broker
                         ↓
                      PostgreSQL
                         ↓
             Ingestion / corporate actions
                         ↓
                    Adjusted OHLCV
                         ↓
                     Feature Store
                         ↓
              ML + LSTM + FinBERT
                         ↓
                   Ensemble Signal
                         ↓
                 No-Code Strategy
                         ↓
             Walk-Forward / Backtest
                         ↓
                Portfolio Risk Engine
                         ↓
                  Paper Trading
                         ↓
             Broker Sandbox / Live
                         ↓
              Reconciliation / Audit
```

PostgreSQL is the system of record; Redis/Celery is the asynchronous job layer.

Live trading remains explicitly gated by provider configuration, broker certification, OOS validation, paper trading, risk limits, reconciliation and manual approval.
