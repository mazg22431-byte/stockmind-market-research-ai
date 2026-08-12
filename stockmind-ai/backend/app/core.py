import os,json,hashlib
from datetime import datetime,timedelta,timezone
from pathlib import Path
from fastapi import HTTPException,Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from pydantic_settings import BaseSettings
from sqlmodel import SQLModel,create_engine,Session,Field
from redis import Redis
from celery import Celery

class Settings(BaseSettings):
    database_url:str="postgresql+psycopg://stockmind:stockmind@postgres:5432/stockmind"
    redis_url:str="redis://redis:6379/0"; jwt_secret:str="CHANGE_ME"; access_token_minutes:int=60
    market_data_base_url:str="";market_data_api_key:str="";corporate_actions_base_url:str="";news_data_base_url:str="";news_data_api_key:str=""
    cors_origins:str="*"
    astro_base_url:str=""
    astro_api_key:str=""
    astro_provider:str="morphemeris"
    astro_timezone:str="Asia/Jakarta"
    astro_default_hour:int=9
    astro_latitude:float=-6.2088
    astro_longitude:float=106.8456
    class Config: env_file=".env"
S=Settings()
engine=create_engine(S.database_url,pool_pre_ping=True)
redis=Redis.from_url(S.redis_url,decode_responses=True)
celery=Celery("stockmind",broker=S.redis_url,backend=S.redis_url)
pwd=CryptContext(schemes=["bcrypt"],deprecated="auto"); oauth=OAuth2PasswordBearer(tokenUrl="/auth/token")
class User(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);email:str=Field(index=True,unique=True);password_hash:str;is_active:bool=True
class ModelVersion(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);ticker:str;name:str;version:str;metrics_json:str;artifact_uri:str;feature_hash:str;status:str="candidate";created_at:datetime=Field(default_factory=datetime.utcnow)
class BacktestRun(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);user_id:int;ticker:str;config_json:str;result_json:str;created_at:datetime=Field(default_factory=datetime.utcnow)
class CorporateAction(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);ticker:str;action_type:str;ex_date:datetime;factor:float=1.;cash_amount:float=0.;source:str=""
def db(): return Session(engine)
def init_db():
    from . import models as _legacy_models
    from . import unified_models as _unified_models
    from . import production_models as _production_models
    from . import trading_models as _trading_models
    SQLModel.metadata.create_all(engine)
def hashpw(x): return pwd.hash(x)
def checkpw(x,h): return pwd.verify(x,h)
def make_token(uid):
    exp=datetime.now(timezone.utc)+timedelta(minutes=S.access_token_minutes)
    return jwt.encode({"sub":str(uid),"exp":exp},S.jwt_secret,algorithm="HS256")
def user(token:str=Depends(oauth)):
    try: uid=int(jwt.decode(token,S.jwt_secret,algorithms=["HS256"])["sub"])
    except Exception: raise HTTPException(401,"Invalid token")
    with db() as s:
        u=s.get(User,uid)
        if not u: raise HTTPException(401,"Unauthorized")
        return u


# Daily AI Breaking News scheduler (05:15 WIB) for the five highest-ranked IDX stories.
try:
    from celery.schedules import crontab
    celery.conf.timezone = "Asia/Jakarta"
    celery.conf.beat_schedule = {
        "stockmind-daily-breaking-news": {
            "task": "app.tasks.daily_breaking_news",
            "schedule": crontab(hour=5, minute=15),
        }
    }
except Exception:
    pass
