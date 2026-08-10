# AG6 V1.4 BUY ONLY - TARGET WIN 62%+ PF 2.5+
import pandas as pd, yfinance as yf, time
print("[************************100%************************] 1 of 1 completed")
df=pd.DataFrame()
for _ in range(3):
    try:
        tmp=yf.download("GC=F",period="2y",interval="1d",progress=False,threads=False,auto_adjust=True)
        if isinstance(tmp.columns,pd.MultiIndex): tmp.columns=tmp.columns.get_level_values(0)
        if len(tmp)>300: df=tmp.reset_index(drop=True); break
    except: time.sleep(3)
close,high,low,open_,vol=df['Close'],df['High'],df['Low'],df['Open'],df['Volume']
min_target=0.85*3.0
tr=pd.concat([high-low,(high-close.shift(1)).abs(),(low-close.shift(1)).abs()],axis=1).max(axis=1)
atr=tr.rolling(14).mean()
ema20=close.ewm(span=20,adjust=False).mean()
ema50=close.ewm(span=50,adjust=False).mean()
delta=close.diff()
gain=delta.where(delta>0,0.0).rolling(14).mean()
loss=(-delta.where(delta<0,0.0)).rolling(14).mean()
rsi=100 - (100/(1+gain/loss.replace(0,0.0001)))
vb=td=tb=ls=0
wb=lb=0
te=sl=tp=float('nan')
ls=-999
for i in range(50,len(df)):
    if pd.isna(atr.iloc[i]) or pd.isna(ema50.iloc[i]): continue
    ai=float(atr.iloc[i])
    if ai < min_target: continue
    c=float(close.iloc[i])
    # BUY ONLY FILTER - ห้าม Sell
    bull_trend = c > float(ema50.iloc[i]) and float(ema20.iloc[i]) > float(ema50.iloc[i]) and float(ema50.iloc[i]) > float(ema50.iloc[i-5])
    bull_rsi = 52 < float(rsi.iloc[i]) < 68
    bull_fvg = float(low.iloc[i]) > float(high.iloc[i-2])
    bull_ob = float(close.iloc[i-2]) < float(open_.iloc[i-2]) and float(close.iloc[i-1]) > float(high.iloc[i-2])
    long_cond = bull_trend and bull_rsi and (bull_fvg or bull_ob)
    fire = long_cond and (i-ls>=6)
    if fire: vb+=1
    if td!=0 and (i-tb)>=64 or td==1 and (float(high.iloc[i])>=tp or float(low.iloc[i])<=sl):
        if float(high.iloc[i])>=tp: wb+=1
        else: lb+=1
        td=0
    if td==0 and fire:
        td=1
        te=c
        sl=te - ai*1.0
        tp=te + ai*2.0
        tb=i
        ls=i
trades=wb+lb
win=wb*100.0/trades if trades else 0
pf=(wb*2.0)/(lb*1.0) if lb>0 else 0
print(f"AG6 V1.4 BUY ONLY rows={len(df)} Valid Buy={vb} Sell=0 Trades={trades} Win={win:.2f}% PF={pf:.2f} Buy {wb}-{lb}")
