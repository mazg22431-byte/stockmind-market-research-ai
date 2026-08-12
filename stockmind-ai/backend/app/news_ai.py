
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
import os, re
import httpx
import xml.etree.ElementTree as ET

IDX_FALLBACK = [
    ("AADI","PT Adaro Andalan Indonesia Tbk"),("ABMM","PT ABM Investama Tbk"),("ACES","PT Aspirasi Hidup Indonesia Tbk"),
    ("ADMR","PT Adaro Minerals Indonesia Tbk"),("ADRO","PT Alamtri Resources Indonesia Tbk"),("AKRA","PT AKR Corporindo Tbk"),
    ("ANTM","PT Aneka Tambang Tbk"),("ASII","PT Astra International Tbk"),("BBCA","PT Bank Central Asia Tbk"),
    ("BBNI","PT Bank Negara Indonesia (Persero) Tbk"),("BBRI","PT Bank Rakyat Indonesia (Persero) Tbk"),("BBTN","PT Bank Tabungan Negara (Persero) Tbk"),
    ("BMRI","PT Bank Mandiri (Persero) Tbk"),("BRIS","PT Bank Syariah Indonesia Tbk"),("BUKA","PT Bukalapak.com Tbk"),
    ("CPIN","PT Charoen Pokphand Indonesia Tbk"),("EMTK","PT Elang Mahkota Teknologi Tbk"),("ERAA","PT Erajaya Swasembada Tbk"),
    ("EXCL","PT XL Axiata Tbk"),("GOTO","PT GoTo Gojek Tokopedia Tbk"),("ICBP","PT Indofood CBP Sukses Makmur Tbk"),
    ("INCO","PT Vale Indonesia Tbk"),("INDF","PT Indofood Sukses Makmur Tbk"),("INKP","PT Indah Kiat Pulp & Paper Tbk"),
    ("INTP","PT Indocement Tunggal Prakarsa Tbk"),("ISAT","PT Indosat Tbk"),("ITMG","PT Indo Tambangraya Megah Tbk"),
    ("JPFA","PT Japfa Comfeed Indonesia Tbk"),("JSMR","PT Jasa Marga (Persero) Tbk"),("KLBF","PT Kalbe Farma Tbk"),
    ("MDKA","PT Merdeka Copper Gold Tbk"),("MEDC","PT Medco Energi Internasional Tbk"),("MIKA","PT Mitra Keluarga Karyasehat Tbk"),
    ("MNCN","PT Media Nusantara Citra Tbk"),("PGAS","PT Perusahaan Gas Negara Tbk"),("PGEO","PT Pertamina Geothermal Energy Tbk"),
    ("PTBA","PT Bukit Asam Tbk"),("PTPP","PT PP (Persero) Tbk"),("SIDO","PT Industri Jamu dan Farmasi Sido Muncul Tbk"),
    ("SMGR","PT Semen Indonesia (Persero) Tbk"),("SMRA","PT Summarecon Agung Tbk"),("SRTG","PT Saratoga Investama Sedaya Tbk"),
    ("TLKM","PT Telkom Indonesia (Persero) Tbk"),("TOWR","PT Sarana Menara Nusantara Tbk"),("UNTR","PT United Tractors Tbk"),
    ("UNVR","PT Unilever Indonesia Tbk"),("WIKA","PT Wijaya Karya (Persero) Tbk"),("WSKT","PT Waskita Karya (Persero) Tbk")
]

HYPE_WORDS = {
    "merger":2.0,"akuisisi":2.2,"kontrak":1.5,"dividen":1.4,"buyback":1.8,"laba":1.4,"tumbuh":1.2,
    "smelter":1.3,"hilirisasi":1.2,"ekspansi":1.1,"izin":1.0,"rights issue":1.3,"spin off":1.1,
    "tambang":1.0,"emas":1.1,"nikel":1.0,"batu bara":.9,"data center":1.2,"cloud":1.0,"ai":1.0,
    "menarik":.6,"bullish":.7,"outlook":.6,"naik":.6,"melonjak":1.0,"terbang":1.2,"volume":.5,
}
POSITIVE = {"positif":1,"naik":1,"menguat":1,"tumbuh":1,"laba":1,"untung":1,"bullish":1,"buyback":1,"dividen":.8,"kontrak":.7,"prospek":.8}
NEGATIVE = {"turun":1,"melemah":1,"rugi":1,"bearish":1,"utang":.7,"gagal":1,"risiko":.5,"anjlok":1}

def _score(text: str, published: datetime) -> tuple[float,float]:
    t=text.lower()
    hype=0.0; pos=0.0; neg=0.0
    for k,v in HYPE_WORDS.items():
        if k in t: hype += v
    for k,v in POSITIVE.items():
        if k in t: pos += v
    for k,v in NEGATIVE.items():
        if k in t: neg += v
    age_h=max(0.0,(datetime.now(timezone.utc)-published.astimezone(timezone.utc)).total_seconds()/3600)
    recency=max(0.0,3.5-age_h*.18)
    sentiment=max(-1.0,min(1.0,(pos-neg)/5.0))
    return round(min(10.0,hype+recency),2), round(sentiment,3)

def _parse_date(x:str)->datetime:
    try: return parsedate_to_datetime(x).astimezone(timezone.utc)
    except Exception: return datetime.now(timezone.utc)

async def _google_news(query:str, limit:int=12):
    url="https://news.google.com/rss/search"
    params={"q":query,"hl":"id","gl":"ID","ceid":"ID:id"}
    async with httpx.AsyncClient(timeout=12,headers={"User-Agent":"StockMind Market Research/1.0"}) as client:
        r=await client.get(url,params=params); r.raise_for_status()
    root=ET.fromstring(r.text)
    out=[]
    for item in root.findall(".//item")[:limit]:
        title=unescape(item.findtext("title") or "").strip()
        link=item.findtext("link") or ""
        source=(item.findtext("source") or "Google News").strip()
        pub=_parse_date(item.findtext("pubDate") or "")
        hype,sent=_score(title,pub)
        out.append({"title":title,"url":link,"source":source,"published_at":pub.isoformat(),
                    "hype_score":hype,"sentiment":sent})
    return out

async def fetch_breaking(symbol:str|None=None, limit:int=30):
    q=(symbol.upper()+" saham IDX OR Bursa Efek Indonesia") if symbol else "(saham OR IHSG OR IDX) Indonesia"
    items=await _google_news(q, max(12,limit))
    for i,x in enumerate(items,1):
        x["rank"]=i; x["symbol"]=symbol.upper() if symbol else None
    return items

async def fetch_hype(limit:int=5):
    universe=IDX_FALLBACK
    # Broad market query first for recency and then ticker-specific query for candidates.
    broad=await _google_news("(IHSG OR saham OR emiten) Indonesia",24)
    candidates=[]
    for x in broad:
        m=re.search(r"\b([A-Z]{4})\b",x["title"])
        if m and any(sym==m.group(1) for sym,_ in universe):
            x["symbol"]=m.group(1); candidates.append(x)
    if len(candidates)<limit:
        for sym,name in universe[:18]:
            try:
                rows=await _google_news(f"{sym} {name} saham",4)
                for x in rows:
                    x["symbol"]=sym; candidates.append(x)
            except Exception:
                continue
            if len(candidates)>=limit*3: break
    uniq={}
    for x in candidates:
        key=(x.get("symbol"), re.sub(r"\W+"," ",x["title"].lower())[:120])
        uniq[key]=x
    ranked=sorted(uniq.values(), key=lambda x:(x.get("hype_score",0),x.get("published_at","")), reverse=True)
    return ranked[:limit]

def _template_post(item, symbol):
    sentiment_label="positif" if item["sentiment"]>0.18 else ("negatif" if item["sentiment"]<-0.18 else "netral")
    return (
        f"🚨 AI BREAKING NEWS — {symbol}\n\n"
        f"{item['title']}\n\n"
        f"Analisa cepat StockMind: sentimen {sentiment_label}, hype score {item['hype_score']}/10. "
        f"Berita ini diprioritaskan karena kombinasi relevansi emiten dan recency. "
        f"Gunakan sebagai bahan screening, bukan sinyal transaksi otomatis.\n\n"
        f"Sumber: {item['source']}\n{item['url']}"
    )

async def auto_posts(limit:int=5):
    rows=await fetch_hype(limit)
    now=datetime.now(timezone.utc).isoformat()
    return [{"id":f"sm-{i+1}-{abs(hash(x['title']))%100000}","symbol":x.get("symbol") or "IDX",
             "published_at":x["published_at"],"source":x["source"],"url":x["url"],
             "title":x["title"],"hype_score":x["hype_score"],"sentiment":x["sentiment"],
             "post":_template_post(x,x.get("symbol") or "IDX"),"generated_at":now} for i,x in enumerate(rows)]

async def ai_ranked_search(symbol:str):
    rows=await fetch_breaking(symbol,18)
    return sorted(rows,key=lambda x:(x["hype_score"],x["published_at"]),reverse=True)
