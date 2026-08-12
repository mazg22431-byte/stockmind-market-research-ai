
import json, math, os
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
import torch
from torch import nn
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from .ml import FEATURES, feat, leakage_folds
from .dl import LSTMClassifier, make_sequences
from .core import db, ModelVersion

REG=Path("model_registry"); REG.mkdir(exist_ok=True)
FINBERT_NAME=os.getenv("FINBERT_MODEL","ProsusAI/finbert")

class FinBERTService:
    _tok=None; _model=None
    @classmethod
    def _load(cls):
        if cls._model is None:
            cls._tok=AutoTokenizer.from_pretrained(FINBERT_NAME)
            cls._model=AutoModelForSequenceClassification.from_pretrained(FINBERT_NAME)
            cls._model.eval()
    @classmethod
    def score(cls, texts):
        if not texts: return {"positive":0.0,"neutral":1.0,"negative":0.0,"score":0.0}
        cls._load()
        batch=cls._tok(texts,return_tensors="pt",padding=True,truncation=True,max_length=256)
        with torch.no_grad(): logits=cls._model(**batch).logits
        p=torch.softmax(logits,dim=-1).mean(0).numpy()
        labels=[cls._model.config.id2label[i].lower() for i in range(len(p))]
        d={k:0.0 for k in ["positive","neutral","negative"]}
        for k,v in zip(labels,p):
            if k in d:d[k]=float(v)
        return {**d,"score":d["positive"]-d["negative"]}

def train_lstm_walkforward(df, lookback=30, epochs=5, hidden=64, lr=1e-3):
    x=feat(df).dropna().reset_index(drop=True)
    folds=leakage_folds(len(x),5,5)
    aucs=[]
    for tr_end,test_start,test_end in folds:
        tr=x.iloc[:tr_end].copy()
        # Sequences are created only from the training prefix; no test observations leak into training.
        Xtr,ytr=make_sequences(tr,FEATURES,lookback)
        if len(Xtr)<20: continue
        model=LSTMClassifier(len(FEATURES),hidden)
        opt=torch.optim.Adam(model.parameters(),lr=lr)
        loss_fn=nn.BCELoss()
        xt=torch.tensor(Xtr); yt=torch.tensor(ytr).view(-1,1)
        model.train()
        for _ in range(epochs):
            opt.zero_grad(); pred=model(xt); loss=loss_fn(pred,yt); loss.backward(); opt.step()
        # Test sequences may use only historical context before each test label.
        test=x.iloc[max(0,test_start-lookback):test_end].copy()
        Xt,ytst=make_sequences(test,FEATURES,lookback)
        if len(Xt)==0: continue
        with torch.no_grad():
            p=model(torch.tensor(Xt)).view(-1).numpy()
        # Align to test labels after lookback.
        yy=ytst
        if len(np.unique(yy))>1:
            from sklearn.metrics import roc_auc_score
            aucs.append(float(roc_auc_score(yy,p)))
    # final model trains on all historical observations for deployment only after validation.
    X,y=make_sequences(x,FEATURES,lookback)
    model=LSTMClassifier(len(FEATURES),hidden)
    opt=torch.optim.Adam(model.parameters(),lr=lr); loss_fn=nn.BCELoss()
    if len(X):
        xt=torch.tensor(X);yt=torch.tensor(y).view(-1,1)
        model.train()
        for _ in range(max(epochs,8)):
            opt.zero_grad();pred=model(xt);loss=loss_fn(pred,yt);loss.backward();opt.step()
    return model, {"mean_auc":float(np.mean(aucs)) if aucs else 0.0,"folds":len(aucs),"lookback":lookback}

def save_lstm(model,ticker,version):
    path=REG/f"{ticker}_{version}_lstm.pt";torch.save(model.state_dict(),path);return str(path)

def ensemble_score(tree_prob, lstm_prob, sentiment_score, weights=(0.45,0.35,0.20)):
    z=weights[0]*tree_prob+weights[1]*lstm_prob+weights[2]*((sentiment_score+1)/2)
    confidence=abs(z-0.5)*2
    signal="BUY" if z>=0.60 else ("SELL" if z<=0.40 else "HOLD")
    return {"score":float(z),"confidence":float(confidence),"signal":signal}

def latest_tree(path, X):
    m=joblib.load(path); return float(m.predict_proba(X[FEATURES].tail(1))[:,1][0])

def latest_lstm(path, df, lookback=30):
    x=feat(df).dropna().reset_index(drop=True)
    X,_=make_sequences(x,FEATURES,lookback)
    if len(X)==0:return 0.5
    m=LSTMClassifier(len(FEATURES));m.load_state_dict(torch.load(path,map_location="cpu"));m.eval()
    with torch.no_grad():return float(m(torch.tensor(X[-1:])).view(-1)[0])

def register_ensemble(ticker,tree_version,tree_path,lstm_path,metrics,weights):
    meta={"components":["tree_ml","lstm","finbert"],"weights":weights,"metrics":metrics}
    v=f"ensemble-{pd.Timestamp.utcnow().strftime('%Y%m%d%H%M%S')}"
    with db() as s:
        s.add(ModelVersion(ticker=ticker,name="ML+LSTM+FinBERT Ensemble",version=v,
                           metrics_json=json.dumps(meta),artifact_uri=json.dumps({"tree":tree_path,"lstm":lstm_path}),
                           feature_hash=",".join(FEATURES),status="candidate"))
        s.commit()
    return v,meta
