# AG6 V1.3 ELITE RSI - TARGET WIN 60%+ PF 2.5+ TRADES 30+
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
vol=df['Volume'] if 'Volume' in df else pd.Series([1]*len(df), index=df.index)
min_target=0.85*3.0
tr=pd.concat([high-low,(high-close.shift(1)).abs(),(low-close.shift(1)).abs()],axis=1).max(axis=1)
atr=tr.rolling(14).mean()
ema50=close.ewm(span=50,adjust=False).mean()
delta=close.diff()
gain=delta.where(delta>0,0.0).rolling(14).mean()
loss=(-delta.where(delta<0,0.0)).rolling(14).mean()
rs= gain / loss.replace(0,0.0001)
rsi=100 - (100/(1+rs))
vb=vs=0
td=0
te=sl=tp=float('nan')
tb=-1
ls=-999
wb=lb=ws=ls2=0
for i in range(50,len(df)):
    if pd.isna(atr.iloc[i]) or pd.isna(ema50.iloc[i]) or pd.isna(rsi.iloc[i]): continue
    ai=float(atr.iloc[i])
    if ai < min_target: continue
    c=float(close.iloc[i])
    r=float(rsi.iloc[i])
    bull_trend = c > float(ema50.iloc[i])
    bear_trend = c < float(ema50.iloc[i])
    bull_rsi = 50 < r < 72
    bear_rsi = 28 < r < 50
    bull_fvg = float(low.iloc[i]) > float(high.iloc[i-2]) and float(close.iloc[i-1]) > float(open_.iloc[i-1])
    bear_fvg = float(high.iloc[i]) < float(low.iloc[i-2]) and float(close.iloc[i-1]) < float(open_.iloc[i-1])
    bull_ob = float(close.iloc[i-2]) < float(open_.iloc[i-2]) and float(close.iloc[i-1]) > float(open_.iloc[i-1]) and float(close.iloc[i-1]) > float(high.iloc[i-2]) and float(vol.iloc[i-1]) > float(vol.iloc[i-2])
    bear_ob = float(close.iloc[i-2]) > float(open_.iloc[i-2]) and float(close.iloc[i-1]) < float(open_.iloc[i-1]) and float(close.iloc[i-1]) < float(low.iloc[i-2]) and float(vol.iloc[i-1]) > float(vol.iloc[i-2])
    long_cond = bull_trend and bull_rsi and (bull_fvg or bull_ob)
    short_cond = bear_trend and bear_rsi and (bear_fvg or bear_ob)
    fire_long = long_cond and (i-ls>=6)
    fire_short = short_cond and (i-ls>=6)
    if fire_long: vb+=1
    if fire_short: vs+=1
    if td!=0:
        et=(i-tb)>=64
        hit_tp=hit_sl=False
        if td==1:
            if float(high.iloc[i])>=tp: hit_tp=True
            if float(low.iloc[i])<=sl: hit_sl=True
        else:
            if float(low.iloc[i])<=tp: hit_tp=True
            if float(high.iloc[i])>=sl: hit_sl=True
        if hit_tp or hit_sl or et:
            if td==1:
                if float(high.iloc[i])>=tp: wb+=1
                else: lb+=1
            else:
                if float(low.iloc[i])<=tp: ws+=1
                else: ls2+=1
            td=0
    if td==0:
        if fire_long:
            td=1
            te=c
            sl=te - ai*1.0
            tp=te + ai*1.9
            tb=i
            ls=i
        elif fire_short:
            td=-1
            te=c
            sl=te + ai*1.0
            tp=te - ai*1.9
            tb=i
            ls=i
trades=wb+lb+ws+ls2
win=(wb+ws)*100.0/trades if trades else 0
pf=((wb+ws)*1.9)/((lb+ls2)*1.0) if (lb+ls2)>0 else 0
print(f"AG6 V1.3 ELITE RSI rows={len(df)} Valid Buy={vb} Sell={vs} Trades={trades} Win={win:.2f}% PF={pf:.2f} Buy {wb}-{lb} Sell {ws}-{ls2}")
