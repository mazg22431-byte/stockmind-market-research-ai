# StockMind AI IDX — Unified v1→v7 Production Readiness

This release implements the control plane for all 15 requested production gates.

1. Broker sandbox/certification
   - `broker_certification.py` runs account, positions, quote, submit/cancel checks.
   - It is a harness; the actual broker contract must be mapped and certified by the broker.

2. Order/fill state machine
   - `order_state.py` enforces CREATED → PENDING_SUBMIT → SUBMITTED → PARTIAL/FILLED/CANCELLED/REJECTED.

3. Broker/PostgreSQL reconciliation
   - `reconciliation.py` and `/api/ops/reconcile` provide the reconciliation job/audit record.
   - Extend the DB portfolio adapter when live broker fills are mapped.

4. Idempotency
   - Client order IDs are generated and audited.
   - Broker-side idempotency must be enabled where the broker supports it.

5. IDX market hours/calendar
   - Regular equity session logic is based on current IDX published trading hours.
   - Official closed days must be supplied in `IDX_CALENDAR_CSV`; never hard-code holidays indefinitely.

6. Stale quote detection
   - `quote_health.py` rejects data older than the configured threshold.

7. Circuit breaker / emergency flatten
   - Global circuit breaker plus emergency flatten endpoint.

8. Monitoring/alerts
   - Webhook alert integration and Celery heartbeat/reconciliation jobs.

9. Vault/KMS
   - `secrets.py` prefers injected environment/file secrets so credentials do not live in source control.
   - In production, use Vault Agent/KMS/secret manager and rotate credentials.

10. Full IDX universe/security master
   - `security_master.py` ingests the licensed provider's full security master into PostgreSQL.

11. Delisted stocks
   - Security status + delisting date are persisted and `tradable()` blocks inactive/delisted symbols.

12. Corporate-action reconciliation
   - `corp_recon.py` compares provider actions with stored actions.

13. Strict OOS validation
   - `oos_validation.py` provides purged/embargoed expanding folds. No random split.

14. Paper trading gate
   - `paper_gate.py` defaults to 60 required trading days before a session can be marked PASSED.

15. Conservative live activation
   - Live mode remains explicit, manual approval is mandatory, and risk limits are enforced.

## Non-negotiable external dependencies

Software cannot manufacture:
- a broker's certification approval
- a licensed IDX data contract
- a licensed news contract
- the official holiday file
- actual broker credentials
- real OOS performance

Those must be supplied by the operator/vendor. The application exposes the interfaces and gates for them.
