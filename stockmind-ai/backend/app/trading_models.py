
from datetime import datetime
from sqlmodel import SQLModel,Field
class TradingConfig(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);user_id:int;mode:str="paper";enabled:bool=False
    max_order_value:float=5_000_000;max_position_pct:float=.10;max_daily_loss_pct:float=.02
    require_manual_approval:bool=True;updated_at:datetime=Field(default_factory=datetime.utcnow)
class OrderAudit(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);user_id:int;client_order_id:str;symbol:str;side:str;quantity:int
    mode:str;status:str;reason:str;payload_json:str;created_at:datetime=Field(default_factory=datetime.utcnow)
