
import json
from datetime import datetime,timezone
from .core import db
from .unified_models import DataSource,Signal,NewsItemUnified,MarketBar,FeatureVector
DEFAULTS=[
("idx_market","market_data","LICENSED_IDX"),("idx_corporate_actions","corporate_actions","LICENSED_IDX"),
("idx_security_master","security_master","LICENSED_IDX"),("idx_calendar","calendar","IDX_OFFICIAL"),
("licensed_news","news","LICENSED_NEWS"),("broker","broker","BROKER")]
def bootstrap():
    with db() as s:
        for n,k,p in DEFAULTS:
            if not s.query(DataSource).filter(DataSource.name==n).first():
                s.add(DataSource(name=n,kind=k,provider=p))
        s.commit()
def ensemble(ml,lstm,finbert):
    score=.45*ml+.35*lstm+.20*((finbert+1)/2)
    signal="BUY" if score>=.60 else "SELL" if score<=.40 else "HOLD"
    return score,signal,min(1,abs(score-.5)*2)
def write_signal(symbol,ml,lstm,finbert,version="production-ensemble"):
    score,sig,conf=ensemble(ml,lstm,finbert)
    with db() as s:
        x=Signal(symbol=symbol,ts=datetime.now(timezone.utc),ml_probability=ml,lstm_probability=lstm,
                 finbert_score=finbert,ensemble_score=score,signal=sig,confidence=conf,model_version=version)
        s.add(x);s.commit();s.refresh(x);return x.model_dump()
def health():
    bootstrap()
    with db() as s:
        return {"market_bars":s.query(MarketBar).count(),"news":s.query(NewsItemUnified).count(),
                "features":s.query(FeatureVector).count(),"signals":s.query(Signal).count()}
