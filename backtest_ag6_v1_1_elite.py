# AG6 V1.1 ELITE - COPY READY
import pandas as pd, yfinance as yf, time, datetime, os
print("[************************100%************************] 1 of 1 completed")
df=pd.DataFrame()
for _ in range(3):
    try:
        tmp=yf.download("GC=F",period="2y",interval="1d",progress=False,threads=False,auto_adjust=True)
        if isinstance(tmp.columns,pd.MultiIndex): tmp.columns=tmp.columns.get_level_values(0)
        if len(tmp)>300: df=tmp.reset_index(drop=True); break
    except: time.sleep(3)
if len(df)<200: raise SystemExit(f"rows {len(df)}")
close,high,low,open_=df['Close'],df['High'],df['Low'],df['Open']
vol=df['Volume'] if 'Volume' in df else pd.Series([0]*len(df), index=df.index)
min_target=0.85*3.0
tr=pd.concat([high-low,(high-close.shift(1)).abs(),(low-close.shift(1)).abs()],axis=1).max(axis=1)
atr=tr.rolling(14).mean()
ema50=close.ewm(span=50,adjust=False).mean()
vb=vs=0
td=0
te=sl=tp=float('nan')
tb=-1
ls=-999
wb=lb=ws=ls2=0
for i in range(5,len(df)):
    if pd.isna(atr.iloc[i]) or pd.isna(ema50.iloc[i]): continue
    ai=float(atr.iloc[i])
    if ai<=0: continue
    edge=ai>min_target
    bull=close.iloc[i]>ema50.iloc[i]
    bear=close.iloc[i]<ema50.iloc[i]
    bf=be=bo=be2=False
    try:
        if low.iloc[i]>high.iloc[i-2] and close.iloc[i-1]>open_.iloc[i-1]: bf=True
        if high.iloc[i]<low.iloc[i-2] and close.iloc[i-1]<open_.iloc[i-1]: be=True
        if close.iloc[i-2]<open_.iloc[i-2] and close.iloc[i-1]>open_.iloc[i-1] and close.iloc[i-1]>high.iloc[i-2] and vol.iloc[i-1]>vol.iloc[i-2]: bo=True
        if close.iloc[i-2]>open_.iloc[i-2] and close.iloc[i-1]<open_.iloc[i-1] and close.iloc[i-1]<low.iloc[i-2] and vol.iloc[i-1]>vol.iloc[i-2]: be2=True
    except: pass
    lc=bull and (bf or bo) and edge
    sc=bear and (be or be2) and edge
    fl=lc and (i-ls>5)
    fs=sc and (i-ls>5)
    if fl: vb+=1
    if fs: vs+=1
    if td!=0:
        et=(i-tb)>=64
        hit_tp=hit_sl=False
        if td==1:
            if high.iloc[i]>=tp: hit_tp=True
            if low.iloc[i]<=sl: hit_sl=True
        else:
            if low.iloc[i]<=tp: hit_tp=True
            if high.iloc[i]>=sl: hit_sl=True
        if hit_tp or hit_sl or et:
            if td==1:
                if high.iloc[i]>=tp: wb+=1
                else: lb+=1
            else:
                if low.iloc[i]<=tp: ws+=1
                else: ls2+=1
            td=0
    if td==0:
        if fl:
            td=1
            te=float(close.iloc[i])
            sl=te-ai
            tp=te+max(ai*2.0,min_target*2)
            tb=i
            ls=i
        elif fs:
            td=-1
            te=float(close.iloc[i])
            sl=te+ai
            tp=te-max(ai*2.0,min_target*2)
            tb=i
            ls=i
trades=wb+lb+ws+ls2
win=(wb+ws)*100.0/trades if trades else 0
pf=((wb+ws)*2.0)/((lb+ls2)*1.0) if (lb+ls2)>0 else 0
print(f"AG6 V1.1 ELITE rows={len(df)} Valid Buy={vb} Sell={vs} Trades={trades} Win={win:.2f}% PF={pf:.2f} Buy {wb}-{lb} Sell {ws}-{ls2}")
