import pandas as pd, numpy as np
from datetime import datetime
from .provider import provider
from .core import db,CorporateAction

REQUIRED={"timestamp","open","high","low","close","volume"}

def normalize_bars(payload):
    rows=payload.get("data",payload if isinstance(payload,list) else [])
    out=[]
    for r in rows:
        x={
            "timestamp":r.get("timestamp") or r.get("datetime") or r.get("date"),
            "open":r.get("open"),"high":r.get("high"),"low":r.get("low"),
            "close":r.get("close"),"volume":r.get("volume",0),
            "adjusted_close":r.get("adjusted_close")
        }
        out.append(x)
    df=pd.DataFrame(out)
    if df.empty: raise ValueError("Provider returned no bars")
    df["timestamp"]=pd.to_datetime(df["timestamp"],utc=True).dt.tz_convert(None)
    for c in ["open","high","low","close","volume","adjusted_close"]:
        if c in df: df[c]=pd.to_numeric(df[c],errors="coerce")
    return df.dropna(subset=["timestamp","open","high","low","close"]).sort_values("timestamp").drop_duplicates("timestamp")

def apply_split_adjustment(df,actions):
    """
    Adjust historical OHLC for split factors. Cash dividends are kept as events;
    total-return analytics should use a separate dividend/total-return series.
    """
    x=df.copy()
    if not actions: return x
    for a in sorted(actions,key=lambda z:z.get("ex_date",""),reverse=True):
        if a.get("action_type","").lower() in {"split","reverse_split","stock_split"}:
            ex=pd.Timestamp(a["ex_date"]); factor=float(a.get("factor",1))
            mask=x["timestamp"]<ex
            if factor>0:
                for c in ["open","high","low","close"]:
                    x.loc[mask,c]=x.loc[mask,c]/factor
                x.loc[mask,"volume"]=x.loc[mask,"volume"]*factor
    return x

async def ingest_idx(ticker,start=None,end=None):
    raw=await provider.bars(ticker,start,end)
    df=normalize_bars(raw)
    try: acts=await provider.corporate_actions(ticker,start,end)
    except Exception: acts=[]
    df=apply_split_adjustment(df,acts)
    with db() as s:
        for a in acts:
            try:
                s.add(CorporateAction(ticker=ticker,action_type=a.get("action_type","unknown"),
                                      ex_date=pd.Timestamp(a["ex_date"]).to_pydatetime(),
                                      factor=float(a.get("factor",1)),cash_amount=float(a.get("cash_amount",0)),
                                      source="licensed_idx_provider"))
            except Exception: pass
        s.commit()
    return df,acts
