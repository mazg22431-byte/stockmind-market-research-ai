import numpy as np
def realistic(df,signal,initial=100_000_000,position_pct=.25,max_positions=4,stop_loss=.05,take_profit=.10,commission_bps=15,slippage_bps=5):
 cash=initial;shares=0.;entry=0.;equity=[];trades=[];peak=initial;maxdd=0
 def cost(x):return x*(commission_bps+slippage_bps)/10000
 for _,r in df.iterrows():
  px=float(r.close)
  if shares and (px/entry-1<=-stop_loss or px/entry-1>=take_profit or not signal(r)):
   gross=shares*px;cash+=gross-cost(gross);trades.append(["SELL",px]);shares=0
  if not shares and signal(r):
   notional=min(cash*position_pct,cash/max_positions);fee=cost(notional);shares=max(0,(notional-fee)/px);cash-=notional;entry=px;trades.append(["BUY",px])
  eq=cash+shares*px;equity.append(eq);peak=max(peak,eq);maxdd=min(maxdd,eq/peak-1)
 if shares:
  gross=shares*float(df.close.iloc[-1]);cash+=gross-cost(gross)
 a=np.array(equity);ret=np.diff(a)/a[:-1] if len(a)>2 else np.array([0])
 return {"initial":initial,"final":float(cash),"return":float(cash/initial-1),"max_drawdown":float(maxdd),"trades":len(trades),"sharpe":float(np.mean(ret)/np.std(ret)*np.sqrt(252)) if np.std(ret)>0 else 0,"commission_bps":commission_bps,"slippage_bps":slippage_bps}
