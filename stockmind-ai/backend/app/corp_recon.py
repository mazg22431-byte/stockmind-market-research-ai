
from .core import db
from .production_models import Security
def reconcile_corporate_actions(provider_actions, stored_actions):
    p={(a.get("symbol"),a.get("ex_date"),a.get("action_type"),a.get("factor"),a.get("cash_amount")) for a in provider_actions}
    s={(a.get("symbol"),a.get("ex_date"),a.get("action_type"),a.get("factor"),a.get("cash_amount")) for a in stored_actions}
    return {"missing_in_db":list(p-s),"unexpected_in_db":list(s-p),"matched":len(p&s)}
