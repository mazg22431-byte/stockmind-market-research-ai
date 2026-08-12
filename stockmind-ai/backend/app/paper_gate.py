
from datetime import datetime
from .core import db
from .production_models import PaperTradingSession
def start(required_days=60):
    with db() as s:
        x=PaperTradingSession(required_days=required_days);s.add(x);s.commit();s.refresh(x)
        return x.model_dump()
def record_day(session_id,metrics):
    with db() as s:
        x=s.get(PaperTradingSession,session_id)
        x.completed_days+=1;x.metrics_json=str(metrics)
        if x.completed_days>=x.required_days:
            x.status="PASSED";x.ended_at=datetime.utcnow()
        s.add(x);s.commit();return x.model_dump()
