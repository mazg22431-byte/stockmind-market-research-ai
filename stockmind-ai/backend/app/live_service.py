
import uuid,json
from .core import db
from .trading import Order,RiskEngine,get_broker
from .trading_models import TradingConfig,OrderAudit

async def submit_signal(user_id,symbol,side,quantity,mode="paper",reason="ensemble_signal"):
    with db() as s:
        cfg=s.query(TradingConfig).filter(TradingConfig.user_id==user_id).first()
    if not cfg: raise RuntimeError("Trading config not initialized")
    if not cfg.enabled: raise RuntimeError("Trading is disabled")
    if cfg.mode!=mode: raise RuntimeError("Requested mode differs from configured mode")
    if cfg.require_manual_approval: raise RuntimeError("Manual approval is required")
    broker=get_broker(mode)
    price=await broker.quote(symbol)
    account=await broker.account()
    positions=await broker.positions()
    current=0
    for p in positions:
        if p.get("symbol")==symbol: current=float(p.get("market_value",0))
    order=Order(symbol=symbol,side=side,quantity=quantity,
                client_order_id="sm-"+uuid.uuid4().hex[:16],reason=reason)
    ok,msg=RiskEngine(cfg.max_order_value,cfg.max_position_pct,cfg.max_daily_loss_pct).approve(
        order,price,account,current,0)
    if not ok: raise RuntimeError(msg)
    result=await broker.submit(order)
    with db() as s:
        s.add(OrderAudit(user_id=user_id,client_order_id=order.client_order_id,symbol=symbol,
                         side=side,quantity=quantity,mode=mode,status=result.get("status","submitted"),
                         reason=reason,payload_json=json.dumps(result)));s.commit()
    return {"order":order.__dict__,"broker_result":result,"risk":"approved"}
