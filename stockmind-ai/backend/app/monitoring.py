
import os,httpx,json,datetime
async def alert(title,message,severity="warning"):
    payload={"title":title,"message":message,"severity":severity,"timestamp":datetime.datetime.utcnow().isoformat()+"Z"}
    url=os.getenv("ALERT_WEBHOOK_URL")
    if not url:return {"sent":False,"reason":"ALERT_WEBHOOK_URL not configured","payload":payload}
    async with httpx.AsyncClient(timeout=10) as c:
        r=await c.post(url,json=payload);r.raise_for_status()
    return {"sent":True}
