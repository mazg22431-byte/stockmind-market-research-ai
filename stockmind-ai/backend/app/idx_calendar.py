
from datetime import datetime, time
from zoneinfo import ZoneInfo
import csv, os

JKT=ZoneInfo("Asia/Jakarta")
# Exchange holiday/closed-day list must be supplied from the licensed/official calendar.
HOLIDAYS=set()
CALENDAR_FILE=os.getenv("IDX_CALENDAR_CSV","/data/idx_calendar.csv")

def load_calendar():
    HOLIDAYS.clear()
    if os.path.exists(CALENDAR_FILE):
        with open(CALENDAR_FILE,encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("is_exchange_day","1") in ("0","false","False"):
                    HOLIDAYS.add(r["trade_date"])

def is_exchange_day(dt):
    d=dt.astimezone(JKT).date()
    return d.weekday()<5 and d.isoformat() not in HOLIDAYS

def regular_session(dt):
    x=dt.astimezone(JKT)
    if not is_exchange_day(x): return False
    wd=x.weekday()
    t=x.time()
    if wd<4: return time(9,0)<=t<=time(12,0) or time(13,30)<=t<=time(16,15)
    return time(9,0)<=t<=time(11,30) or time(14,0)<=t<=time(16,15)

def session_name(dt):
    x=dt.astimezone(JKT)
    if not is_exchange_day(x): return "CLOSED"
    if regular_session(x):
        if x.time()<time(12,0): return "SESSION_I"
        return "SESSION_II"
    return "CLOSED"

load_calendar()
