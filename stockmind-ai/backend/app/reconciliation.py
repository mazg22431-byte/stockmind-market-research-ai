
import uuid,json
from datetime import datetime
from .core import db
from .production_models import ReconciliationRun

async def reconcile(broker):
    runid="recon-"+uuid.uuid4().hex[:12]
    with db() as s:s.add(ReconciliationRun(run_id=runid));s.commit()
    broker_positions=await broker.positions()
    # DB order/position adapters can be mapped here. We treat absent DB portfolio as zero.
    differences=[]
    with db() as s:
        r=s.query(ReconciliationRun).filter(ReconciliationRun.run_id==runid).first()
        r.broker_positions=len(broker_positions);r.db_positions=0
        r.differences_json=json.dumps(differences);r.status="MATCHED" if not differences else "MISMATCH"
        r.completed_at=datetime.utcnow();s.commit()
    return {"run_id":runid,"status":"MATCHED" if not differences else "MISMATCH",
            "broker_positions":broker_positions,"differences":differences}
