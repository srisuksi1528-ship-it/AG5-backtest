# ELITE V2 SMC + e-FCD - SEPARATE COMPARE
import pandas as pd, yfinance as yf, time, datetime, os, math
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
p_friction=0.85
min_rr=3.0
min_target=p_friction*min_rr
tr1=high-low
tr2=(high-close.shift(1)).abs()
tr3=(low-close.shift(1)).abs()
tr=pd.concat([tr1,tr2,tr3],axis=1).max(axis=1)
atr=tr.rolling(14).mean()
ema50=close.ewm(span=50,adjust=False).mean()
valid_buy=0
valid_sell=0
trade_dir=0
trade_entry=float('nan')
trade_sl=float('nan')
trade_tp=float('nan')
trade_bar=-1
last_sig=-999
w_b=l_b=w_s=l_s=0
for i in range(5, len(df)):
    if pd.isna(atr.iloc[i]) or pd.isna(ema50.iloc[i]): continue
    atr_i=float(atr.iloc[i])
    if atr_i<=0: continue
    edge_valid=atr_i > min_target
    h4_ema=float(ema50.iloc[i])
    h4_bullish=float(close.iloc[i]) > h4_ema
    h4_bearish=float(close.iloc[i]) < h4_ema
    bull_fvg=False
    bear_fvg=False
    bull_ob=False
    bear_ob=False
    try:
        if float(low.iloc[i]) > float(high.iloc[i-2]) and float(close.iloc[i-1]) > float(open_.iloc[i-1]): bull_fvg=True
        if float(high.iloc[i]) < float(low.iloc[i-2]) and float(close.iloc[i-1]) < float(open_.iloc[i-1]): bear_fvg=True
        if float(close.iloc[i-2]) < float(open_.iloc[i-2]) and float(close.iloc[i-1]) > float(open_.iloc[i-1]) and float(close.iloc[i-1]) > float(high.iloc[i-2]) and float(vol.iloc[i-1]) > float(vol.iloc[i-2]): bull_ob=True
        if float(close.iloc[i-2]) > float(open_.iloc[i-2]) and float(close.iloc[i-1]) < float(open_.iloc[i-1]) and float(close.iloc[i-1]) < float(low.iloc[i-2]) and float(vol.iloc[i-1]) > float(vol.iloc[i-2]): bear_ob=True
    except: pass
    long_cond=h4_bullish and (bull_fvg or bull_ob) and edge_valid
    short_cond=h4_bearish and (bear_fvg or bear_ob) and edge_valid
    fire_long=long_cond and (i-last_sig>5)
    fire_short=short_cond and (i-last_sig>5)
    if fire_long: valid_buy+=1
    if fire_short: valid_sell+=1
    if trade_dir!=0:
        exit_tp=exit_sl=False
        exit_time=(i-trade_bar)>=64
        if trade_dir==1:
            if float(high.iloc[i])>=trade_tp: exit_tp=True
            if float(low.iloc[i])<=trade_sl: exit_sl=True
        else:
            if float(low.iloc[i])<=trade_tp: exit_tp=True
            if float(high.iloc[i])>=trade_sl: exit_sl=True
        if exit_tp or exit_sl or exit_time:
            if trade_dir==1:
                if float(high.iloc[i])>=trade_tp: w_b+=1
                else: l_b+=1
            else:
                if float(low.iloc[i])<=trade_tp: w_s+=1
                else: l_s+=1
            trade_dir=0
    if trade_dir==0:
        if fire_long:
            trade_dir=1
            trade_entry=float(close.iloc[i])
            trade_sl=trade_entry - atr_i
            trade_tp=trade_entry + max(atr_i*2.0, min_target*2)
            trade_bar=i
            last_sig=i
        elif fire_short:
            trade_dir=-1
            trade_entry=float(close.iloc[i])
            trade_sl=trade_entry + atr_i
            trade_tp=trade_entry - max(atr_i*2.0, min_target*2)
            trade_bar=i
            last_sig=i
trades=w_b+l_b+w_s+l_s
win=(w_b+w_s)*100.0/trades if trades else 0
pf=((w_b+w_s)*2.0)/((l_b+l_s)*1.0) if (l_b+l_s)>0 else 0
print(f"ELITE V2 (ชื่อเดิม: AG5 V20.3 Scoring/BOS/Retest M15) rows={len(df)} Valid Buy={valid_buy} Sell={valid_sell} Trades={trades} Win={win:.2f}% PF={pf:.2f} Buy {w_b}-{l_b} Sell {w_s}-{l_s}")
today=datetime.datetime.now().strftime("%Y-%m-%d")
path="HISTORY_ELITE_V2.csv"
new=not os.path.exists(path)
with open(path,"a",newline="",encoding="utf-8") as f:
    import csv
    w=csv.writer(f)
    if new: w.writerow(["date","rows","valid_buy","valid_sell","trades","winrate","pf","code"])
    w.writerow([today,len(df),valid_buy,valid_sell,trades,f"{win:.2f}",f"{pf:.2f}","ELITE V2"])
