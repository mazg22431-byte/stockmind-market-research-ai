from pathlib import Path
import hashlib,json,joblib,numpy as np,pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from .core import db,ModelVersion
FEATURES=["rsi","macd","signal","ma20","ma50","vol_ratio","ret1"]; ART=Path("model_registry");ART.mkdir(exist_ok=True)
def feat(df):
 x=df.copy();d=x.close.diff();g=d.clip(lower=0).rolling(14).mean();l=(-d.clip(upper=0)).rolling(14).mean()
 x["rsi"]=100-100/(1+g/l.replace(0,np.nan));e12=x.close.ewm(span=12,adjust=False).mean();e26=x.close.ewm(span=26,adjust=False).mean()
 x["macd"]=e12-e26;x["signal"]=x.macd.ewm(span=9,adjust=False).mean();x["ma20"]=x.close.rolling(20).mean();x["ma50"]=x.close.rolling(50).mean();x["vol_ratio"]=x.volume/x.volume.rolling(20).mean();x["ret1"]=x.close.pct_change();x["target"]=(x.close.shift(-5)>x.close).astype(int);return x
def leakage_folds(n,k=5,embargo=5):
 step=n//(k+1);out=[]
 for i in range(k):
  tr=(i+1)*step;ts=tr+embargo;te=min(n,ts+step)
  if ts<te:out.append((tr,ts,te))
 return out
def train_from_csv(ticker,csv_path):
 df=pd.read_csv(csv_path,parse_dates=["timestamp"]);df=feat(df).dropna();aucs=[]
 for tr,ts,te in leakage_folds(len(df)):
  m=HistGradientBoostingClassifier(random_state=42).fit(df[FEATURES].iloc[:tr],df.target.iloc[:tr])
  p=m.predict_proba(df[FEATURES].iloc[ts:te])[:,1]
  if len(set(df.target.iloc[ts:te]))>1:aucs.append(roc_auc_score(df.target.iloc[ts:te],p))
 m=HistGradientBoostingClassifier(random_state=42).fit(df[FEATURES],df.target);v="v"+pd.Timestamp.utcnow().strftime("%Y%m%d%H%M%S");path=ART/f"{ticker}_{v}.joblib";joblib.dump(m,path)
 metrics={"mean_auc":float(np.mean(aucs)) if aucs else 0,"folds":len(aucs),"leakage":"expanding+embargo"}
 with db() as s:s.add(ModelVersion(ticker=ticker,name="HistGradientBoosting",version=v,metrics_json=json.dumps(metrics),artifact_uri=str(path),feature_hash=hashlib.sha256(",".join(FEATURES).encode()).hexdigest()));s.commit()
 return {"version":v,"metrics":metrics}
