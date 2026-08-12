import hashlib,json
from pathlib import Path
import pandas as pd
from .ml import feat,FEATURES
ROOT=Path("feature_store");ROOT.mkdir(exist_ok=True)
def build(ticker,df):
    x=feat(df).dropna()
    meta={"ticker":ticker,"features":FEATURES,"rows":len(x),
          "feature_hash":hashlib.sha256(",".join(FEATURES).encode()).hexdigest()}
    x.to_parquet(ROOT/f"{ticker}.parquet",index=False)
    (ROOT/f"{ticker}.json").write_text(json.dumps(meta))
    return meta
def load(ticker):
    return pd.read_parquet(ROOT/f"{ticker}.parquet")
