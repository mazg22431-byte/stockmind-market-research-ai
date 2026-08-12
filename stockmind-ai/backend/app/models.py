
from datetime import datetime
from sqlmodel import SQLModel, Field
class PriceBar(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);ticker:str=Field(index=True)
    timestamp:datetime=Field(index=True);open:float;high:float;low:float;close:float;volume:float=0
class NewsItem(SQLModel,table=True):
    id:int|None=Field(default=None,primary_key=True);ticker:str=Field(index=True)
    title:str;url:str="";published_at:datetime=Field(default_factory=datetime.utcnow)
    sentiment:float=0;label:str="neutral"
