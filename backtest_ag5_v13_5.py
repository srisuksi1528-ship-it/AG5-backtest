# AG5 v13.5 Forward-Test Logger (ชื่อเดิม: AG5 Forward-Test Logger v13.5 - EMA close+Pivot+Session)
import pandas as pd, yfinance as yf, time, datetime, os
print("[************************100%************************] 1 of 1 completed")
df=pd.DataFrame()
for i in range(3):
    try:
        tmp=yf.download("GC=F",period="2y",interval="1d",progress=False,threads=False,auto_adjust=True)
        if isinstance(tmp.columns,pd.MultiIndex): tmp.columns=tmp.columns.get_level_values(0)
        if len(tmp)>200: df=tmp.reset_index(drop=True); break
    except: time.sleep(3)
if len(df)<200: raise SystemExit(f"rows {len(df)} <200")

close,high,low=df['Close'],df['High'],df['Low']
p_pivot_l,p_pivot_r=5,5
p_base=30
p_reward,p_risk=2.0,1.0

ema_trend=close.ewm(span=p_base,adjust=False).mean()
trend_up=(close>ema_trend).fillna(False)

tr1=high-low
tr2=(high-close.shift(1)).abs()
tr3=(low-close.shift(1)).abs()
tr=pd.concat([tr1,tr2,tr3],axis=1).max(axis=1)
atr=tr.rolling(p_base).mean()

ph=pd.Series(False,index=df.index)
pl=pd.Series(False,index=df.index)
for i in range(p_pivot_l,len(df)-p_pivot_r):
    if high.iloc[i]==high.iloc[i-p_pivot_l:i+p_pivot_r+1].max(): ph.iloc[i+p_pivot_r]=True
    if low.iloc[i]==low.iloc[i-p_pivot_l:i+p_pivot_r+1].min(): pl.iloc[i+p_pivot_r]=True

vb_list=[bool(pl.iloc[i]) and bool(trend_up.iloc[i]) for i in range(len(df))]
vs_list=[bool(ph.iloc[i]) and not bool(trend_up.iloc[i]) for i in range(len(df))]

# backtest single pending
stop=target=None
side=None
pend=False
w_b=l_b=w_s=l_s=0
for i in range(len(df)-1):
    if pend:
        if side=='BUY':
            if low.iloc[i]<=stop: l_b+=1; pend=False
            elif high.iloc[i]>=target: w_b+=1; pend=False
        else:
            if high.iloc[i]>=stop: l_s+=1; pend=False
            elif low.iloc[i]<=target: w_s+=1; pend=False
    if not pend:
        if vb_list[i] and not pd.isna(atr.iloc[i]) and atr.iloc[i]>0:
            c=float(close.iloc[i]); a=float(atr.iloc[i])
            stop=c-a*p_risk; target=c+a*p_reward; side='BUY'; pend=True
        elif vs_list[i] and not pd.isna(atr.iloc[i]) and atr.iloc[i]>0:
            c=float(close.iloc[i]); a=float(atr.iloc[i])
            stop=c+a*p_risk; target=c-a*p_reward; side='SELL'; pend=True

trades=w_b+l_b+w_s+l_s
win=(w_b+w_s)*100.0/trades if trades else 0
pf=((w_b+w_s)*p_reward)/((l_b+l_s)*p_risk) if (l_b+l_s)>0 else 0
print(f"v13.5 (ชื่อเดิม: v13.5 Forward-Test Logger EMA+Pivot+Session) rows={len(df)} Valid Buy={sum(vb_list)} Sell={sum(vs_list)} Trades={trades} Win={win:.2f}% PF={pf:.2f} Buy {w_b}-{l_b} Sell {w_s}-{l_s}")

today=datetime.datetime.now().strftime("%Y-%m-%d")
path="HISTORY_AG5_V13_5.csv"
new=not os.path.exists(path)
with open(path,"a",newline="",encoding="utf-8") as f:
    import csv
    w=csv.writer(f)
    if new: w.writerow(["date","rows","valid_buy","valid_sell","trades","winrate","pf","code"])
    w.writerow([today,len(df),sum(vb_list),sum(vs_list),trades,f"{win:.2f}",f"{pf:.2f}","v13.5"])
