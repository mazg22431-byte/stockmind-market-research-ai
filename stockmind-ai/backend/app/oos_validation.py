
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score,accuracy_score
def purged_walk_forward(df,train_days=504,test_days=63,embargo_days=5):
    df=df.sort_values("timestamp").reset_index(drop=True)
    folds=[];i=train_days
    while i+embargo_days+test_days<=len(df):
        folds.append((df.iloc[:i],df.iloc[i+embargo_days:i+embargo_days+test_days]))
        i+=test_days
    return folds

def evaluate_predictions(y,p):
    return {"auc":float(roc_auc_score(y,p)) if len(set(y))>1 else None,
            "accuracy":float(accuracy_score(y,(np.asarray(p)>=.5).astype(int))),
            "n":len(y)}
