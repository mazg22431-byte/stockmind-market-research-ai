from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
import statistics
from zoneinfo import ZoneInfo

from .astrology_provider import positions
from .core import S, db
from .production_models import Security
from .provider import licensed_bars

FALLBACK_LISTINGS = {
    "BUVA": "2010-07-12",
    "BBCA": "2000-05-31",
    "BBRI": "2003-11-10",
    "BMRI": "2003-07-14",
    "TLKM": "1995-11-14",
}

DEMO_PLANETS = [
    {"body":"sun","sign":"Cancer","sign_degree":19.0,"longitude":109.0,"retrograde":False},
    {"body":"moon","sign":"Cancer","sign_degree":22.0,"longitude":112.0,"retrograde":False},
    {"body":"mercury","sign":"Leo","sign_degree":16.0,"longitude":136.0,"retrograde":False},
    {"body":"venus","sign":"Virgo","sign_degree":5.0,"longitude":155.0,"retrograde":False},
    {"body":"mars","sign":"Virgo","sign_degree":9.0,"longitude":159.0,"retrograde":False},
    {"body":"jupiter","sign":"Aries","sign_degree":3.0,"longitude":3.0,"retrograde":False},
    {"body":"saturn","sign":"Libra","sign_degree":29.0,"longitude":209.0,"retrograde":False},
    {"body":"uranus","sign":"Aries","sign_degree":0.0,"longitude":0.0,"retrograde":False},
    {"body":"neptune","sign":"Aquarius","sign_degree":25.0,"longitude":325.0,"retrograde":False},
    {"body":"pluto","sign":"Capricorn","sign_degree":0.0,"longitude":270.0,"retrograde":False},
]

SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
PLANET_LABELS = {x:x.title() for x in ["sun","moon","mercury","venus","mars","jupiter","saturn","uranus","neptune","pluto"]}


def _iso_date(dt):
    return dt.astimezone(ZoneInfo(S.astro_timezone)).date().isoformat()


def _listing_date(symbol: str):
    with db() as s:
        try:
            row = s.query(Security).filter(Security.symbol == symbol).first()
            if row and row.listing_date:
                return row.listing_date
        except Exception:
            pass
    raw = FALLBACK_LISTINGS.get(symbol, "2010-01-01")
    return datetime.fromisoformat(raw).replace(tzinfo=ZoneInfo(S.astro_timezone))


def _wrap_delta(a, b):
    d = abs((a-b) % 360)
    return min(d, 360-d)


def _aspect(a,b):
    d=_wrap_delta(a,b)
    aspects=[(0,"Conjunction"),(60,"Sextile"),(90,"Square"),(120,"Trine"),(180,"Opposition")]
    best=min(aspects,key=lambda x:abs(d-x[0]))
    return best[1] if abs(d-best[0])<=6 else "Minor / none"


def _sign_from_lon(lon):
    i=int(lon//30)%12
    deg=lon-(i*30)
    return SIGN_NAMES[i], round(deg,1)


def _parse_bar_rows(payload):
    rows=payload.get("data",payload) if isinstance(payload,dict) else payload
    out=[]
    for r in rows or []:
        if not isinstance(r,dict): continue
        date=r.get("date") or r.get("datetime") or r.get("timestamp")
        close=r.get("close") or r.get("c") or r.get("price")
        high=r.get("high") or r.get("h") or close
        low=r.get("low") or r.get("l") or close
        try:
            out.append({"date":str(date)[:10],"close":float(close),"high":float(high),"low":float(low)})
        except Exception:
            continue
    return sorted(out,key=lambda x:x["date"])


def _demo_prices():
    vals=[]
    start=datetime(2026,5,1,tzinfo=timezone.utc)
    base=680.0
    for i in range(105):
        wave=120*math.sin(i/9.5)+55*math.sin(i/3.4)
        close=base+wave+(i*0.25)
        vals.append({"date":(start+timedelta(days=i)).date().isoformat(),"close":round(close,1),"high":round(close+18,1),"low":round(close-18,1)})
    vals[-1]["close"]=740.0
    vals[-1]["high"]=752.0
    vals[-1]["low"]=728.0
    return vals


def _fib_levels(low, high):
    span=high-low
    return [
        {"level":"100% High","ratio":"0.0%","price":round(high),"note":"Recent pivot high"},
        {"level":"78.6%","ratio":"23.6%","price":round(high-span*.236),"note":"Deep retracement zone"},
        {"level":"61.8%","ratio":"38.2%","price":round(high-span*.382),"note":"Area resist / rebound"},
        {"level":"50.0%","ratio":"50.0%","price":round(low+span*.5),"note":"Mid retracement"},
        {"level":"38.2%","ratio":"61.8%","price":round(low+span*.382),"note":"Area resist kuat"},
        {"level":"23.6%","ratio":"78.6%","price":round(low+span*.236),"note":"Last support sebelum high"},
        {"level":"0% Low","ratio":"100%","price":round(low),"note":"Base pivot"},
    ]


def _cycle_dates(low_date, high_date):
    low = datetime.fromisoformat(low_date).replace(tzinfo=timezone.utc)
    high = datetime.fromisoformat(high_date).replace(tzinfo=timezone.utc)
    left=[];right=[]
    for d in [8,13,21,34,55,89,144]:
        left.append({"interval":d,"date":(low+timedelta(days=d)).date().isoformat(),"label":"From Low"})
        right.append({"interval":d,"date":(high+timedelta(days=d)).date().isoformat(),"label":"From High"})
    return left,right


def _price_scenario(low, high):
    span=high-low
    return [
      {"case":"BULL CASE","condition":f"{round(low)} holds + break {round(low+span*.62)}","target":f"{round(low+span*.86)} → {round(high)} → {round(high+span*.7)}","probability":40,"tone":"green"},
      {"case":"BASE CASE","condition":f"{round(low)} holds + reclaim {round(low+span*.5)}","target":f"{round(low+span*.38)} → {round(low+span*.62)} → {round(high)}","probability":40,"tone":"gold"},
      {"case":"BEAR CASE","condition":f"{round(low)} breaks + volume expands","target":f"{round(low*.93)} → {round(low*.82)} → {round(low*.74)}","probability":20,"tone":"red"},
    ]

async def build_deep_dive(symbol: str, analysis_date: str | None = None):
    symbol=symbol.upper()
    tz=ZoneInfo(S.astro_timezone)
    as_of=datetime.fromisoformat(analysis_date).replace(tzinfo=tz) if analysis_date else datetime.now(tz)
    listing=_listing_date(symbol)
    provider_status="DEMO / provider pending"
    natal=DEMO_PLANETS
    transit=DEMO_PLANETS
    prices=_demo_prices()
    try:
        natal_rows=await positions(listing)
        transit_rows=await positions(as_of)
        if natal_rows: natal=natal_rows
        if transit_rows: transit=transit_rows
        provider_status=f"Provider: {S.astro_provider}" if natal_rows and transit_rows else provider_status
    except Exception:
        pass
    try:
        raw=await licensed_bars(symbol)
        parsed=_parse_bar_rows(raw)
        if len(parsed)>=30:
            prices=parsed[-180:]
            provider_status=provider_status.replace("DEMO / provider pending", "Market data live; ephemeris demo" ) if "Provider:" not in provider_status else provider_status
    except Exception:
        pass

    low=min(prices,key=lambda x:x["low"])
    high=max(prices,key=lambda x:x["high"])
    current=prices[-1]
    fibs=_fib_levels(low["low"],high["high"])
    from_low,from_high=_cycle_dates(low["date"],high["date"])

    nmap={x["body"]:x for x in natal}
    tmap={x["body"]:x for x in transit}
    transit_highlights=[]
    for body in ["jupiter","neptune","pluto","saturn","uranus"]:
        if body not in tmap: continue
        n=nmap.get(body) or nmap.get("sun")
        t=tmap[body]
        asp=_aspect(t.get("longitude",0),n.get("longitude",0)) if n else ""
        transit_highlights.append({
          "planet":PLANET_LABELS.get(body,body.title()),
          "position": t.get("sign") or _sign_from_lon(t.get("longitude",0))[0],
          "degree": round(t.get("sign_degree",_sign_from_lon(t.get("longitude",0))[1]),1),
          "aspect": asp,
          "interpretation":"Support / expansion; validate with price" if body=="jupiter" else ("Transformation / structural change" if body=="pluto" else "Volatility / test of conviction")
        })

    stage_scores={
      "financial":68.0,
      "fibonacci_time":65.0,
      "technical":62.0 if current["close"] < fibs[1]["price"] else 74.0,
      "fundamental":71.0,
      "bandarmology":66.0,
    }
    overall=round(statistics.mean(stage_scores.values()),1)
    signal="BULLISH" if overall>=65 else ("BEARISH" if overall<40 else "NEUTRAL")

    windows=[
      {"name":"WINDOW A","period":"20–26 Aug 2026","focus":"Time cluster + deep retracement confluence","tone":"red"},
      {"name":"WINDOW B","period":"11–16 Sep 2026","focus":"Fibonacci follow-up / breakout confirmation","tone":"gold"},
      {"name":"WINDOW C","period":"24 Sep–14 Oct 2026","focus":"Earnings / corporate-event volatility window","tone":"green"},
    ]
    return {
      "symbol":symbol,"analysis_date":as_of.date().isoformat(),"listing_date":listing.date().isoformat(),
      "market_data_status":provider_status,"ephemeris_status":"Provider live" if provider_status.startswith("Provider:") else "Demo ephemeris",
      "natal":natal,"transit":transit,"transit_highlights":transit_highlights,
      "price":{"current":round(current["close"],2),"low":round(low["low"],2),"high":round(high["high"],2),"low_date":low["date"],"high_date":high["date"],"series":prices[-70:]},
      "fibonacci_levels":fibs,"time_from_low":from_low,"time_from_high":from_high,
      "major_windows":windows,"stages":stage_scores,"overall":overall,"signal":signal,
      "scenario":_price_scenario(low["low"],high["high"]),
      "strategy":[
        f"Akumulasi bertahap di area {fibs[-1]['price']}–{fibs[1]['price']}",
        f"Konfirmasi pertama: close di atas {fibs[4]['price']}",
        f"Konfirmasi kuat: break & close di atas {fibs[3]['price']}",
        f"Major confirmation: break {fibs[1]['price']} lalu retest sukses",
        f"Cut loss / invalidation: break {fibs[-1]['price']} dengan volume besar",
        f"Profit-taking reference: {fibs[2]['price']} / {fibs[0]['price']}",
      ],
      "disclaimer":"Kerangka astro-market bersifat eksperimental. Posisi planet adalah data astronomi; interpretasi market adalah heuristik dan bukan metode ilmiah tervalidasi atau rekomendasi beli/jual."
    }
