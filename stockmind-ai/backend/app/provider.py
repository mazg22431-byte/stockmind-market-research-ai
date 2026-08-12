import httpx, os
from .core import S

class IDXLicensedProvider:
    """
    Production adapter for an IDX-licensed feed.
    Configure the exact vendor URL/field mapping in environment variables.
    This deliberately does not scrape IDX or use an unofficial feed.
    """
    async def bars(self,ticker,start=None,end=None):
        if not S.market_data_base_url or not S.market_data_api_key:
            raise RuntimeError("Licensed IDX provider not configured.")
        params={"symbol":ticker}
        if start: params["start"]=start
        if end: params["end"]=end
        async with httpx.AsyncClient(timeout=30) as c:
            r=await c.get(S.market_data_base_url,params=params,
                          headers={"Authorization":f"Bearer {S.market_data_api_key}"})
            r.raise_for_status()
            return r.json()

    async def corporate_actions(self,ticker,start=None,end=None):
        url=S.corporate_actions_base_url
        if not url or not S.market_data_api_key:
            raise RuntimeError("Corporate-actions endpoint not configured for licensed provider.")
        params={"symbol":ticker}
        if start: params["start"]=start
        if end: params["end"]=end
        async with httpx.AsyncClient(timeout=30) as c:
            r=await c.get(url,params=params,
                          headers={"Authorization":f"Bearer {S.market_data_api_key}"})
            r.raise_for_status()
            return r.json()

    async def news(self,ticker,limit=20):
        if not S.news_data_base_url or not S.news_data_api_key:
            return []
        async with httpx.AsyncClient(timeout=30) as c:
            r=await c.get(S.news_data_base_url,
                          params={"symbol":ticker,"limit":limit},
                          headers={"Authorization":f"Bearer {S.news_data_api_key}"})
            r.raise_for_status()
            return r.json()

provider=IDXLicensedProvider()

async def licensed_bars(ticker,start=None,end=None):
    return await provider.bars(ticker,start,end)

async def licensed_news(ticker,limit=20):
    return await provider.news(ticker,limit)
