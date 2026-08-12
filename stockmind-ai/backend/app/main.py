
from fastapi import FastAPI,Depends,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel,EmailStr,Field
import json
from .core import S,init_db,db,User,BacktestRun,hashpw,checkpw,make_token,user
from .tasks import ingest_train_ensemble
from .provider import licensed_bars,licensed_news
from .trading_models import TradingConfig,OrderAudit
from .production_models import Security
from .unified_models import Signal,DataSource,NewsItemUnified,StrategyDefinition,PortfolioSnapshot
from .platform import bootstrap,health as platform_health
from .news_ai import fetch_breaking, fetch_hype, auto_posts, ai_ranked_search, IDX_FALLBACK
from .bandar_detector import analyze as analyze_bandarmology
from .screener_presets import list_presets
from .astro_deep_dive import build_deep_dive
app=FastAPI(title="StockMind AI IDX",version="7.0-integrated")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in S.cors_origins.split(",")],allow_methods=["*"],allow_headers=["*"])
@app.on_event("startup")
def startup(): init_db(); bootstrap()
@app.get("/health")
def health(): return {"status":"ok","platform":platform_health(),"database":"postgresql","queue":"redis/celery"}

class Register(BaseModel): email:EmailStr; password:str
@app.post("/auth/register")
def register(x:Register):
    with db() as s:
        if s.query(User).filter(User.email==x.email).first(): raise HTTPException(409,"Email exists")
        u=User(email=x.email,password_hash=hashpw(x.password));s.add(u);s.commit();s.refresh(u);return {"id":u.id}
@app.post("/auth/token")
def login(f:OAuth2PasswordRequestForm=Depends()):
    with db() as s:
        u=s.query(User).filter(User.email==f.username).first()
        if not u or not checkpw(f.password,u.password_hash): raise HTTPException(401,"Invalid credentials")
        return {"access_token":make_token(u.id),"token_type":"bearer"}

@app.get("/api/provider/bars/{ticker}")
async def bars(ticker,me=Depends(user)): return await licensed_bars(ticker)
@app.get("/api/provider/news/{ticker}")
async def news(ticker,me=Depends(user)): return await licensed_news(ticker)

@app.post("/jobs/ingest-train-ensemble/{ticker}")
def queue(ticker,me=Depends(user)):
    t=ingest_train_ensemble.delay(ticker)
    return {"job_id":t.id,"status":"queued","pipeline":"licensed IDX → corporate actions → adjusted prices → features → ML + LSTM → FinBERT → ensemble → registry"}

class BT(BaseModel):
    ticker:str;initial:float=100_000_000;position_pct:float=.25;max_positions:int=4
    stop_loss:float=.05;take_profit:float=.10;commission_bps:float=15;slippage_bps:float=5;rules:list[dict]=[]
@app.post("/api/backtest/config")
def backtest_config(x:BT,me=Depends(user)):
    from .strategy import validate
    validate(x.rules)
    r={"ticker":x.ticker,"initial":x.initial,"costs":{"commission_bps":x.commission_bps,"slippage_bps":x.slippage_bps},
       "risk":{"position_pct":x.position_pct,"max_positions":x.max_positions,"stop_loss":x.stop_loss,"take_profit":x.take_profit},
       "rules":x.rules,"status":"configured"}
    with db() as s:
        s.add(BacktestRun(user_id=me.id,ticker=x.ticker,config_json=x.model_dump_json(),result_json=json.dumps(r)));s.commit()
    return r

class SignalRequest(BaseModel):
    ticker:str;tree_probability:float=.5;lstm_probability:float=.5;sentiment_score:float=0
@app.post("/api/ensemble/score")
def score(x:SignalRequest,me=Depends(user)):
    from .ensemble import ensemble_score
    return {"ticker":x.ticker,**ensemble_score(x.tree_probability,x.lstm_probability,x.sentiment_score)}

@app.get("/api/platform/health")
def ph(me=Depends(user)): return {"status":"ok","pipeline":platform_health()}
@app.get("/api/platform/sources")
def sources(me=Depends(user)):
    with db() as s:return [x.model_dump() for x in s.query(DataSource).all()]
@app.get("/api/platform/ranking")
def ranking(limit:int=50,me=Depends(user)):
    with db() as s:return [x.model_dump() for x in s.query(Signal).order_by(Signal.ensemble_score.desc()).limit(min(limit,200)).all()]
@app.get("/api/platform/signals")
def signals(symbol:str|None=None,limit:int=100,me=Depends(user)):
    with db() as s:
        q=s.query(Signal).order_by(Signal.ts.desc())
        if symbol:q=q.filter(Signal.symbol==symbol.upper())
        return [x.model_dump() for x in q.limit(min(limit,500)).all()]
@app.get("/api/platform/news")
def platform_news(symbol:str|None=None,limit:int=50,me=Depends(user)):
    with db() as s:
        q=s.query(NewsItemUnified).order_by(NewsItemUnified.published_at.desc())
        if symbol:q=q.filter(NewsItemUnified.symbol==symbol.upper())
        return [x.model_dump() for x in q.limit(min(limit,200)).all()]

class Strategy(BaseModel):
    name:str;version:str="1.0";rules:list[dict]=[]
@app.post("/api/strategy")
def save_strategy(x:Strategy,me=Depends(user)):
    from .strategy import validate
    validate(x.rules)
    with db() as s:
        obj=StrategyDefinition(name=x.name,version=x.version,rules_json=json.dumps(x.rules))
        s.add(obj);s.commit();s.refresh(obj);return obj.model_dump()
@app.get("/api/strategy")
def strategies(me=Depends(user)):
    with db() as s:return [x.model_dump() for x in s.query(StrategyDefinition).all()]

class TradingSetup(BaseModel):
    mode:str="paper";enabled:bool=False;max_order_value:float=5_000_000;max_position_pct:float=.10
    max_daily_loss_pct:float=.02;require_manual_approval:bool=True
@app.post("/api/trading/config")
def trading_config(x:TradingSetup,me=Depends(user)):
    if x.mode not in ("paper","live"): raise HTTPException(400,"mode must be paper or live")
    if x.mode=="live" and not x.require_manual_approval: raise HTTPException(400,"Manual approval is mandatory")
    with db() as s:
        c=s.query(TradingConfig).filter(TradingConfig.user_id==me.id).first() or TradingConfig(user_id=me.id)
        for k,v in x.model_dump().items(): setattr(c,k,v)
        s.add(c);s.commit();s.refresh(c);return c.model_dump()
@app.get("/api/trading/status")
def trading_status(me=Depends(user)):
    with db() as s:
        c=s.query(TradingConfig).filter(TradingConfig.user_id==me.id).first()
        return {"configured":bool(c),**(c.model_dump() if c else {"mode":"paper","enabled":False})}

class OrderReq(BaseModel):
    symbol:str;side:str;quantity:int;mode:str="paper";reason:str="manual_or_ensemble"
@app.post("/api/trading/order")
async def trading_order(x:OrderReq,me=Depends(user)):
    if x.side not in ("BUY","SELL") or x.quantity<=0: raise HTTPException(400,"Invalid order")
    from .live_service import submit_signal
    try:return await submit_signal(me.id,x.symbol.upper(),x.side,x.quantity,x.mode,x.reason)
    except RuntimeError as e: raise HTTPException(409,str(e))

@app.get("/api/ops/broker-certification")
async def broker_certification(me=Depends(user)):
    from .broker_certification import run_sandbox_certification
    return await run_sandbox_certification()
@app.get("/api/ops/reconcile")
async def reconcile(me=Depends(user)):
    from .trading import get_broker
    from .reconciliation import reconcile
    return await reconcile(get_broker("live"))
@app.post("/api/ops/circuit-breaker/{scope}")
async def breaker(scope:str,me=Depends(user)):
    from .circuit_breaker import trigger
    return await trigger(scope,"operator/manual trigger")
@app.post("/api/ops/circuit-breaker/{scope}/reset")
async def reset(scope:str,me=Depends(user)):
    from .circuit_breaker import reset
    return await reset(scope,str(me.id))
@app.post("/api/ops/emergency-flatten")
async def flatten(me=Depends(user)):
    from .trading import get_broker
    from .circuit_breaker import trigger,emergency_flatten
    b=get_broker("live");await trigger("GLOBAL","emergency flatten")
    return {"circuit_breaker":True,"orders":await emergency_flatten(b,await b.positions())}
@app.post("/api/ops/paper/start")
def paper_start(days:int=60,me=Depends(user)):
    from .paper_gate import start
    return start(days)
@app.get("/api/ops/calendar/{date}")
def calendar(date:str,me=Depends(user)):
    from datetime import datetime
    from .idx_calendar import is_exchange_day,session_name
    dt=datetime.fromisoformat(date).replace(tzinfo=__import__("zoneinfo").ZoneInfo("Asia/Jakarta"))
    return {"date":date,"exchange_day":is_exchange_day(dt),"session":session_name(dt)}
@app.get("/api/ops/security/{symbol}")
def security(symbol:str,me=Depends(user)):
    from .security_master import tradable
    with db() as s:
        x=s.query(Security).filter(Security.symbol==symbol.upper()).first()
        return {"symbol":symbol.upper(),"exists":bool(x),"tradable":tradable(symbol),
                "security":x.model_dump() if x else None}

# --- StockMind Market Research extensions ---
@app.get("/api/idx/universe")
def idx_universe(me=Depends(user)):
    try:
        with db() as s:
            rows=s.query(Security).filter(Security.status=="ACTIVE").order_by(Security.symbol).all()
            if rows:
                return [{"symbol":x.symbol,"name":x.name,"board":x.board} for x in rows]
    except Exception:
        pass
    return [{"symbol":s,"name":n,"board":"IDX"} for s,n in IDX_FALLBACK]

@app.get("/api/breaking-news")
async def breaking_news(symbol:str|None=None,limit:int=30,me=Depends(user)):
    return await fetch_breaking(symbol, min(max(limit,1),50))

@app.get("/api/breaking-news/hype")
async def breaking_news_hype(limit:int=5,me=Depends(user)):
    return await fetch_hype(min(max(limit,1),5))

@app.get("/api/breaking-news/posts")
async def breaking_news_posts(limit:int=5,me=Depends(user)):
    from .core import redis
    cached=redis.get("stockmind:breaking-news:daily")
    if cached:
        try:
            rows=json.loads(cached)
            return rows[:min(max(limit,1),5)]
        except Exception:
            pass
    rows=await auto_posts(min(max(limit,1),5))
    try: redis.setex("stockmind:breaking-news:daily",24*60*60,json.dumps(rows))
    except Exception: pass
    return rows

@app.get("/api/breaking-news/search/{symbol}")
async def breaking_news_search(symbol:str,me=Depends(user)):
    return await ai_ranked_search(symbol.upper())

@app.get("/api/bandarmology/{symbol}")
def bandarmology(symbol:str,me=Depends(user)):
    return analyze_bandarmology(symbol.upper())

@app.get("/api/screener/presets")
def screener_presets(me=Depends(user)):
    return list_presets()

class AstroReq(BaseModel):
    symbol:str
    analysis_date:str
    financial_score:float=50
    fibonacci_time_score:float=50
    technical_score:float=50
    fundamental_score:float=50
    bandarmology_score:float=50

@app.post("/api/astrology/analyze")
def astrology_analysis(x:AstroReq,me=Depends(user)):
    # Experimental heuristic only; this is not a scientifically validated predictive method.
    scores=[x.financial_score,x.fibonacci_time_score,x.technical_score,x.fundamental_score,x.bandarmology_score]
    overall=round(sum(scores)/len(scores),1)
    signal="BULLISH" if overall>=65 else ("BEARISH" if overall<40 else "NEUTRAL")
    return {"symbol":x.symbol.upper(),"analysis_date":x.analysis_date,"method":"StockMind Experimental Astro-Market 5 Stage",
            "scientific_status":"Experimental heuristic; not scientifically validated",
            "stages":[
              {"name":"Financial","score":x.financial_score},
              {"name":"Fibonacci Time","score":x.fibonacci_time_score},
              {"name":"Technical","score":x.technical_score},
              {"name":"Fundamental","score":x.fundamental_score},
              {"name":"Bandarmology","score":x.bandarmology_score}],
            "overall":overall,"signal":signal}


@app.get("/api/astrology/deep-dive/{symbol}")
async def astrology_deep_dive(symbol:str, analysis_date:str|None=None, me=Depends(user)):
    try:
        return await build_deep_dive(symbol.upper(), analysis_date)
    except Exception as e:
        raise HTTPException(502, f"Astrology deep dive provider error: {e}")

@app.get("/api/dashboard/{ticker}")
def dashboard(ticker:str,me=Depends(user)):
    with db() as s:
        q=s.query(Signal).filter(Signal.symbol==ticker.upper()).order_by(Signal.ts.desc()).first()
        return {"ticker":ticker.upper(),
                "signal":q.signal if q else "HOLD","confidence":q.confidence if q else 0,
                "components":{"ml":q.ml_probability if q else .5,"lstm":q.lstm_probability if q else .5,
                              "finbert":q.finbert_score if q else 0},
                "ensemble_score":q.ensemble_score if q else .5,
                "charts":{"equity_curve":[],"drawdown":[]}}
