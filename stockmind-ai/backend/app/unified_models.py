
from datetime import datetime
from sqlmodel import SQLModel,Field
class DataSource(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);name:str=Field(unique=True,index=True)
    kind:str;provider:str="";license_ref:str="";enabled:bool=True;status:str="READY";last_sync:datetime|None=None
class MarketBar(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);symbol:str=Field(index=True);ts:datetime=Field(index=True)
    open:float;high:float;low:float;close:float;volume:float;adjusted_close:float|None=None
    source:str="";corporate_action_adjusted:bool=False
class CorporateActionUnified(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);symbol:str=Field(index=True);ex_date:str=Field(index=True)
    action_type:str;factor:float|None=None;cash_amount:float|None=None;source:str="";reconciled:bool=False
class NewsItemUnified(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);symbol:str|None=Field(default=None,index=True)
    published_at:datetime=Field(index=True);title:str;body:str="";source:str="";url:str=""
    sentiment:float|None=None;finbert_label:str|None=None;ingested_at:datetime=Field(default_factory=datetime.utcnow)
class FeatureVector(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);symbol:str=Field(index=True);ts:datetime=Field(index=True)
    feature_version:str;values_json:str
class Signal(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);symbol:str=Field(index=True);ts:datetime=Field(index=True)
    ml_probability:float;lstm_probability:float;finbert_score:float;ensemble_score:float
    signal:str;confidence:float;model_version:str
class StrategyDefinition(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);name:str;version:str;rules_json:str;enabled:bool=True
class BacktestRunUnified(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);strategy_id:int;symbol_universe_json:str
    started_at:datetime=Field(default_factory=datetime.utcnow);ended_at:datetime|None=None
    metrics_json:str="{}";equity_curve_json:str="[]";drawdown_json:str="[]";status:str="QUEUED"
class PortfolioSnapshot(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);ts:datetime=Field(index=True);cash:float;equity:float
    gross_exposure:float;net_exposure:float;drawdown:float;mode:str="paper"
class TradeFillUnified(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);client_order_id:str=Field(index=True)
    broker_order_id:str="";symbol:str=Field(index=True);side:str;quantity:int;price:float
    commission:float=0;slippage:float=0;filled_at:datetime=Field(default_factory=datetime.utcnow)
    mode:str="paper";raw_json:str="{}"
