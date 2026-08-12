
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Literal
import os, uuid, json
import httpx

Side=Literal["BUY","SELL"]
Mode=Literal["paper","live"]

@dataclass
class Order:
    symbol:str
    side:Side
    quantity:int
    order_type:str="MARKET"
    limit_price:float|None=None
    client_order_id:str=""
    reason:str="model_signal"

@dataclass
class Account:
    cash:float
    buying_power:float
    equity:float

class RiskEngine:
    def __init__(self,max_order_value=5_000_000,max_position_pct=.10,max_daily_loss_pct=.02):
        self.max_order_value=max_order_value
        self.max_position_pct=max_position_pct
        self.max_daily_loss_pct=max_daily_loss_pct

    def approve(self,order:Order,price:float,account:Account,current_position_value=0,daily_pnl=0):
        notional=order.quantity*price
        if order.quantity<=0:return False,"quantity must be positive"
        if notional>self.max_order_value:return False,"order exceeds max order value"
        if account.equity>0 and (current_position_value+notional)/account.equity>self.max_position_pct and order.side=="BUY":
            return False,"position exposure limit"
        if account.equity>0 and daily_pnl/account.equity<=-self.max_daily_loss_pct:
            return False,"daily loss kill switch"
        if order.side=="BUY" and notional>account.buying_power:
            return False,"insufficient buying power"
        return True,"approved"

class BrokerAdapter:
    """Vendor-neutral broker contract. Map this interface to the broker's authenticated trading API."""
    async def account(self)->Account: raise NotImplementedError
    async def quote(self,symbol:str)->float: raise NotImplementedError
    async def submit(self,order:Order)->dict: raise NotImplementedError
    async def cancel(self,broker_order_id:str)->dict: raise NotImplementedError
    async def positions(self)->list[dict]: raise NotImplementedError

class HttpBroker(BrokerAdapter):
    def __init__(self):
        self.base=os.getenv("BROKER_BASE_URL","")
        self.key=os.getenv("BROKER_API_KEY","")
        self.secret=os.getenv("BROKER_API_SECRET","")
    def headers(self):
        return {"Authorization":f"Bearer {self.key}","X-API-SECRET":self.secret}
    async def _get(self,path,params=None):
        if not self.base: raise RuntimeError("BROKER_BASE_URL is not configured")
        async with httpx.AsyncClient(timeout=20) as c:
            r=await c.get(self.base+path,params=params,headers=self.headers());r.raise_for_status();return r.json()
    async def _post(self,path,payload):
        if not self.base: raise RuntimeError("BROKER_BASE_URL is not configured")
        async with httpx.AsyncClient(timeout=20) as c:
            r=await c.post(self.base+path,json=payload,headers=self.headers());r.raise_for_status();return r.json()
    async def account(self):
        x=await self._get("/account");return Account(float(x["cash"]),float(x["buying_power"]),float(x["equity"]))
    async def quote(self,symbol): return float((await self._get("/quote",{"symbol":symbol}))["price"])
    async def submit(self,order): return await self._post("/orders",asdict(order))
    async def cancel(self,broker_order_id): return await self._post(f"/orders/{broker_order_id}/cancel",{})
    async def positions(self): return await self._get("/positions")

class PaperBroker(BrokerAdapter):
    def __init__(self):
        self.cash=float(os.getenv("PAPER_INITIAL_CASH","100000000"));self.prices={}
        self.orders=[]
    async def account(self):
        return Account(self.cash,self.cash,self.cash)
    async def quote(self,symbol):
        # Paper mode requires quote ingestion from the licensed market-data feed.
        raise RuntimeError("Paper quote must be supplied by the market-data service; no synthetic price is used.")
    async def submit(self,order):
        oid="paper-"+uuid.uuid4().hex[:12]
        self.orders.append({"id":oid,**asdict(order),"status":"accepted","created_at":datetime.now(timezone.utc).isoformat()})
        return self.orders[-1]
    async def cancel(self,broker_order_id): return {"id":broker_order_id,"status":"cancelled"}
    async def positions(self): return []

def get_broker(mode:Mode):
    return PaperBroker() if mode=="paper" else HttpBroker()
