
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from .ml import feat, FEATURES, leakage_folds
from .strategy import evaluate, validate
def run(df,rules,initial=100_000_000,windows=5):
    validate(rules)
    x=feat(df).dropna(subset=FEATURES).reset_index(drop=True)
    folds=leakage_folds(len(x),windows,5)
    equity=initial; out=[]
    for i,(tr_end,test_start,test_end) in enumerate(folds,1):
        tr=x.iloc[:tr_end]; te=x.iloc[test_start:test_end]
        m=GradientBoostingClassifier(random_state=42).fit(tr[FEATURES],tr.target)
        p=m.predict_proba(te[FEATURES])[:,1]
        cash=equity; shares=0.; entry=0.; trades=0
        for j,(_,r) in enumerate(te.iterrows()):
            sig=evaluate(r,rules,float(p[j]),.5,0)
            if sig and shares==0: shares=cash/r.close; cash=0; entry=r.close; trades+=1
            elif shares and (r.close<entry*.95 or r.rsi>70):
                cash=shares*r.close; shares=0
        if shares: cash=shares*te.close.iloc[-1]
        equity=float(cash)
        out.append({"fold":i,"train_end":str(tr.timestamp.iloc[-1].date()),
                    "test_start":str(te.timestamp.iloc[0].date()),
                    "test_end":str(te.timestamp.iloc[-1].date()),
                    "equity":equity,"trades":trades})
    return {"initial":initial,"final":equity,"return":equity/initial-1,"folds":out}
