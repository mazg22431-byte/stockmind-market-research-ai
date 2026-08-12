
from .core import celery
@celery.task
def health_check():
    from .monitoring import alert
    import asyncio
    return asyncio.run(alert("StockMind worker heartbeat","Worker is alive","info"))
@celery.task
def reconcile_live():
    from .trading import get_broker
    from .reconciliation import reconcile
    import asyncio
    return asyncio.run(reconcile(get_broker("live")))
