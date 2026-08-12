
from datetime import datetime
from .core import db
from .production_models import CircuitBreaker
async def trigger(scope,reason):
    with db() as s:
        c=s.query(CircuitBreaker).filter(CircuitBreaker.scope==scope).first()
        if not c:c=CircuitBreaker(scope=scope)
        c.enabled=False;c.reason=reason;c.triggered_at=datetime.utcnow();s.add(c);s.commit()
    return {"scope":scope,"enabled":False,"reason":reason}
async def reset(scope,operator):
    with db() as s:
        c=s.query(CircuitBreaker).filter(CircuitBreaker.scope==scope).first()
        if not c:return {"scope":scope,"enabled":True}
        c.enabled=True;c.reset_by=operator;c.reason="";s.add(c);s.commit()
    return {"scope":scope,"enabled":True}
async def emergency_flatten(broker,positions):
    results=[]
    for p in positions:
        q=int(abs(float(p.get("quantity",0))))
        if q<=0:continue
        side="SELL" if float(p.get("quantity",0))>0 else "BUY"
        from .trading import Order
        o=Order(symbol=p["symbol"],side=side,quantity=q,client_order_id="FLAT-"+p["symbol"])
        try:results.append(await broker.submit(o))
        except Exception as e:results.append({"symbol":p["symbol"],"error":str(e)})
    return results
