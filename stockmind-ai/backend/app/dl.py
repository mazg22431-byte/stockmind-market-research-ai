import numpy as np, torch
from torch import nn
class LSTMClassifier(nn.Module):
    def __init__(self,n_features,hidden=64):
        super().__init__();self.lstm=nn.LSTM(n_features,hidden,batch_first=True);self.fc=nn.Linear(hidden,1)
    def forward(self,x):
        y,_=self.lstm(x);return torch.sigmoid(self.fc(y[:,-1]))
def make_sequences(df,features,lookback=30):
    X=df[features].to_numpy(dtype="float32"); y=df["target"].to_numpy(dtype="float32")
    xs=[];ys=[]
    for i in range(lookback,len(df)):
        xs.append(X[i-lookback:i]);ys.append(y[i])
    return np.asarray(xs),np.asarray(ys)
