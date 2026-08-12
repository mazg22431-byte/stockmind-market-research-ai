
import os, httpx
async def news(ticker: str, limit=20):
    key=os.getenv("NEWSAPI_KEY","").strip()
    if not key: return []
    url="https://newsapi.org/v2/everything"
    params={"q":f'"{ticker.upper()}" stock OR shares OR earnings',
            "language":"en","sortBy":"publishedAt","pageSize":limit,"apiKey":key}
    async with httpx.AsyncClient(timeout=15) as c:
        r=await c.get(url,params=params); r.raise_for_status()
        return [{"title":a.get("title",""),"url":a.get("url",""),
                 "published_at":a.get("publishedAt")} for a in r.json().get("articles",[])]
