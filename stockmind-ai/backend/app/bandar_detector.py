
from __future__ import annotations
from datetime import datetime, timezone
import hashlib, math, random

BROKERS=[("YP","Maybank Sekuritas"),("CC","Mandiri Sekuritas"),("ZP","Mirae Asset"),("AK","UBS Sekuritas"),("BK","J.P. Morgan Sekuritas"),("NI","BNI Sekuritas"),("DX","Bahana"),("PD","Indo Premier")]
def _seed(symbol):
    return int(hashlib.sha256(symbol.encode()).hexdigest()[:8],16)
def analyze(symbol:str):
    rnd=random.Random(_seed(symbol.upper()))
    buy=[]; sell=[]
    for code,name in BROKERS:
        b=round(rnd.uniform(2,18),2); s=round(rnd.uniform(1,16),2)
        buy.append({"code":code,"name":name,"buy":b,"sell":s,"net":round(b-s,2)})
        sell.append({"code":code,"name":name,"buy":s,"sell":b,"net":round(s-b,2)})
    buy=sorted(buy,key=lambda x:x["net"],reverse=True)
    flow=round(sum(x["net"] for x in buy),2)
    dist=round((max([x["net"] for x in buy])-min([x["net"] for x in buy]))/3+50,1)
    return {"symbol":symbol.upper(),"asof":datetime.now(timezone.utc).isoformat(),"data_status":"DEMO / provider pending",
            "broker_summary":buy,"broker_distribution":{"accumulation":dist,"distribution":round(100-dist,1)},
            "broker_flow":flow,"trade_flow":{"foreign":round(rnd.uniform(-20,20),2),"retail":round(rnd.uniform(-20,20),2),"institution":round(rnd.uniform(-20,20),2)},
            "fundachart":{"eps_growth":round(rnd.uniform(-8,24),1),"roe":round(rnd.uniform(7,24),1),"revenue_growth":round(rnd.uniform(-5,22),1)},
            "ai_score":round(max(0,min(100,50+flow*1.8)),1)}
