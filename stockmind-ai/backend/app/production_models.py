
from datetime import datetime
from sqlmodel import SQLModel, Field

class Security(SQLModel, table=True):
    id:int|None=Field(default=None,primary_key=True)
    symbol:str=Field(index=True,unique=True)
    name:str=""
    board:str=""
    status:str="ACTIVE"
    listing_date:datetime|None=None
    delisting_date:datetime|None=None
    currency:str="IDR"
    lot_size:int=100
    source:str="licensed_provider"
    updated_at:datetime=Field(default_factory=datetime.utcnow)

class TradingCalendarDay(SQLModel, table=True):
    id:int|None=Field(default=None,primary_key=True)
    trade_date:str=Field(index=True,unique=True)
    is_exchange_day:bool=True
    source:str="IDX"
    notes:str=""

class QuoteHealth(SQLModel, table=True):
    id:int|None=Field(default=None,primary_key=True)
    symbol:str=Field(index=True)
    asof:datetime
    received_at:datetime=Field(default_factory=datetime.utcnow)
    age_seconds:float=0
    stale:bool=False
    source:str="licensed_provider"

class CircuitBreaker(SQLModel, table=True):
    id:int|None=Field(default=None,primary_key=True)
    scope:str=Field(index=True)
    enabled:bool=True
    reason:str=""
    triggered_at:datetime|None=None
    reset_by:str=""

class ReconciliationRun(SQLModel, table=True):
    id:int|None=Field(default=None,primary_key=True)
    run_id:str=Field(index=True,unique=True)
    started_at:datetime=Field(default_factory=datetime.utcnow)
    completed_at:datetime|None=None
    status:str="RUNNING"
    broker_open_orders:int=0
    db_open_orders:int=0
    broker_positions:int=0
    db_positions:int=0
    differences_json:str="[]"

class PaperTradingSession(SQLModel, table=True):
    id:int|None=Field(default=None,primary_key=True)
    started_at:datetime=Field(default_factory=datetime.utcnow)
    ended_at:datetime|None=None
    required_days:int=60
    completed_days:int=0
    status:str="RUNNING"
    metrics_json:str="{}"

class ValidationRun(SQLModel, table=True):
    id:int|None=Field(default=None,primary_key=True)
    model_version:str
    started_at:datetime=Field(default_factory=datetime.utcnow)
    status:str="RUNNING"
    train_end:str=""
    oos_start:str=""
    oos_end:str=""
    metrics_json:str="{}"
    passed:bool=False
