
from datetime import datetime
from .core import db
from .production_models import Security

def sync_security_master(rows,source="licensed_provider"):
    n=0
    with db() as s:
        for r in rows:
            sym=r["symbol"].upper()
            obj=s.query(Security).filter(Security.symbol==sym).first()
            if not obj: obj=Security(symbol=sym)
            for k in ["name","board","status","currency","lot_size"]:
                if k in r:setattr(obj,k,r[k])
            for k in ["listing_date","delisting_date"]:
                if r.get(k):setattr(obj,k,datetime.fromisoformat(r[k]))
            obj.source=source;obj.updated_at=datetime.utcnow()
            s.add(obj);n+=1
        s.commit()
    return n

def tradable(symbol):
    with db() as s:
        x=s.query(Security).filter(Security.symbol==symbol.upper()).first()
        return bool(x and x.status=="ACTIVE" and x.delisting_date is None)
