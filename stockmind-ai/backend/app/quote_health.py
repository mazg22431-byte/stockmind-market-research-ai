
from datetime import datetime,timezone
from .production_models import QuoteHealth

def check_quote(asof, max_age_seconds=30):
    now=datetime.now(timezone.utc)
    if asof.tzinfo is None: asof=asof.replace(tzinfo=timezone.utc)
    age=max(0,(now-asof).total_seconds())
    return age, age>max_age_seconds
