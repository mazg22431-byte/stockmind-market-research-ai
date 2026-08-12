
import asyncio, json, os, uuid
from .trading import get_broker,Order

REQUIRED=["account","quote","positions","submit","cancel"]
async def run_sandbox_certification():
    mode="paper" if os.getenv("BROKER_SANDBOX","1")=="1" else "live"
    broker=get_broker(mode)
    results=[]
    async def test(name,fn):
        try: await fn(); results.append({"test":name,"passed":True})
        except Exception as e: results.append({"test":name,"passed":False,"error":str(e)})
    await test("account",broker.account)
    await test("positions",broker.positions)
    symbol=os.getenv("CERT_SYMBOL","BBCA")
    await test("quote",lambda: broker.quote(symbol))
    async def order_test():
        o=Order(symbol=symbol,side="BUY",quantity=int(os.getenv("CERT_QTY","1")),
                client_order_id="CERT-"+uuid.uuid4().hex[:16],reason="sandbox_certification")
        r=await broker.submit(o)
        if r.get("id"): await broker.cancel(r["id"])
    await test("submit_then_cancel",order_test)
    return {"mode":mode,"passed":all(x["passed"] for x in results),"results":results}
