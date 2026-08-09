# AG5 v14.9-C (ชื่อโค้ดเดิม: AG5 Observation Layer v14.9-C [ALLGOLD] - Pivot+HTF+Cooldown)
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
p_reward,p_risk,p_friction=2.0,1.0,15.0
p_cooldown=10

ema_base=close.ewm(span=p_base,adjust=False).mean()
htf_close=close.shift(1)
htf_ema=ema_base.shift(1)
trend_up=(htf_close>htf_ema).fillna(False)

tr1=high-low
tr2=(high-close.shift(1)).abs()
tr3=(low-close.shift(1)).abs()
tr=pd.concat([tr1,tr2,tr3],axis=1).max(axis=1)
atr=tr.rolling(p_base).mean()
edge_valid=(atr*p_reward - p_friction)>0
edge_valid=edge_valid.fillna(False)

ph=pd.Series(False,index=df.index)
pl=pd.Series(False,index=df.index)
for i in range(p_pivot_l,len(df)-p_pivot_r):
    if high.iloc[i]==high.iloc[i-p_pivot_l:i+p_pivot_r+1].max(): ph.iloc[i+p_pivot_r]=True
    if low.iloc[i]==low.iloc[i-p_pivot_l:i+p_pivot_r+1].min(): pl.iloc[i+p_pivot_r]=True

last_buy=-999999
last_sell=-999999
vb_list=[]
vs_list=[]
for i in range(len(df)):
    raw_sell=bool(ph.iloc[i]) and not bool(trend_up.iloc[i])
    raw_buy=bool(pl.iloc[i]) and bool(trend_up.iloc[i])
    buy_ok=(i-last_buy)>=p_cooldown
    sell_ok=(i-last_sell)>=p_cooldown
    vb=raw_buy and bool(edge_valid.iloc[i]) and buy_ok
    vs=raw_sell and bool(edge_valid.iloc[i]) and sell_ok
    if vb: last_buy=i
    if vs: last_sell=i
    vb_list.append(vb)
    vs_list.append(vs)

# outcome tracking single pending per dir
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
print(f"v14.9-C (ชื่อเดิม: v14.9-C [ALLGOLD] Pivot+HTF+Cooldown) rows={len(df)} Valid Buy={sum(vb_list)} Sell={sum(vs_list)} Trades={trades} Win={win:.2f}% PF={pf:.2f} Buy {w_b}-{l_b} Sell {w_s}-{l_s}")

today=datetime.datetime.now().strftime("%Y-%m-%d")
path="HISTORY_AG5_V14_9_C.csv"
new=not os.path.exists(path)
with open(path,"a",newline="",encoding="utf-8") as f:
    import csv
    w=csv.writer(f)
    if new: w.writerow(["date","rows","valid_buy","valid_sell","trades","winrate","pf","code"])
    w.writerow([today,len(df),sum(vb_list),sum(vs_list),trades,f"{win:.2f}",f"{pf:.2f}","v14.9-C"])
