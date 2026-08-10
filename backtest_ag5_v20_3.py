# AG5 V20.3 (ชื่อเดิม: AG5 V20.3 - Scoring/BOS/Retest/H4 Regime M15 design - converted to Daily)
import pandas as pd, yfinance as yf, time, datetime, os, math
print("[************************100%************************] 1 of 1 completed")
df=pd.DataFrame()
for _ in range(3):
    try:
        tmp=yf.download("GC=F",period="2y",interval="1d",progress=False,threads=False,auto_adjust=True)
        if isinstance(tmp.columns,pd.MultiIndex): tmp.columns=tmp.columns.get_level_values(0)
        if len(tmp)>200: df=tmp.reset_index(drop=True); break
    except: time.sleep(3)
if len(df)<200: raise SystemExit(f"rows {len(df)}")

close,high,low,open_=df['Close'],df['High'],df['Low'],df['Open']
vol=df['Volume'] if 'Volume' in df else pd.Series([0]*len(df))

p_thresh=70.0
p_w_trend,p_w_struct,p_w_mom,p_w_vol,p_w_liq=25.0,25.0,20.0,15.0
p_risk_mult,p_reward_mult=1.0,2.0
p_max_dur=64
p_retest_mult,p_disp_mult,p_break_mult=0.20,0.50,0.10
p_bos_max=32

ema50=close.ewm(span=50,adjust=False).mean()
ema200=close.ewm(span=200,adjust=False).mean()
tr1=high-low
tr2=(high-close.shift(1)).abs()
tr3=(low-close.shift(1)).abs()
tr=pd.concat([tr1,tr2,tr3],axis=1).max(axis=1)
atr_raw=tr.rolling(14).mean()
atr=atr_raw
atr_sma=atr_raw.rolling(50).mean()
vol_sma=vol.rolling(20).mean()

ph_bool=[False]*len(df)
pl_bool=[False]*len(df)
ph_val=[float('nan')]*len(df)
pl_val=[float('nan')]*len(df)
for i in range(5,len(df)-5):
    win_h=high.iloc[i-5:i+6].max()
    if high.iloc[i]==win_h:
        ph_bool[i+5]=True
        ph_val[i+5]=float(high.iloc[i])
    win_l=low.iloc[i-5:i+6].min()
    if low.iloc[i]==win_l:
        pl_bool[i+5]=True
        pl_val[i+5]=float(low.iloc[i])

res_arr=[]
sup_arr=[]
bos_bull_bar=-999
bos_bear_bar=-999
bos_bull_level=float('nan')
bos_bear_level=float('nan')
last_long=-999999
last_short=-999999
valid_buy=0
valid_sell=0
trades_log=[]
trade_dir=0
trade_entry=trade_sl=trade_tp=float('nan')
trade_bar=-1
w_b=l_b=w_s=l_s=0

for i in range(len(df)):
    if ph_bool[i]:
        res_arr.insert(0, ph_val[i])
        if len(res_arr)>3: res_arr.pop()
    if pl_bool[i]:
        sup_arr.insert(0, pl_val[i])
        if len(sup_arr)>3: sup_arr.pop()
    res_level=res_arr[0] if len(res_arr)>0 else float('nan')
    sup_level=sup_arr[0] if len(sup_arr)>0 else float('nan')
    if pd.isna(atr.iloc[i]) or pd.isna(ema50.iloc[i]): continue
    atr_i=float(atr.iloc[i])
    if atr_i<=0: continue
    atr_sma_i=float(atr_sma.iloc[i]) if not pd.isna(atr_sma.iloc[i]) else atr_i
    vol_ok=atr_i>0 and atr_i>(atr_sma_i*0.7)
    if i==0: continue
    h4_close=float(close.iloc[i-1])
    h4_fast=float(ema50.iloc[i-1])
    h4_slow=float(ema200.iloc[i-1]) if not pd.isna(ema200.iloc[i-1]) else h4_fast
    h4_regime=0
    if h4_close>h4_slow and h4_fast>h4_slow: h4_regime=1
    elif h4_close<h4_slow and h4_fast<h4_slow: h4_regime=-1
    body=abs(float(close.iloc[i]-open_.iloc[i]))
    is_displace=body>(atr_i*p_disp_mult)
    hl=float(high.iloc[i]-low.iloc[i])
    is_strong_up= (hl>0 and ((float(close.iloc[i]-low.iloc[i])/hl)>0.6 and float(close.iloc[i])>float(open_.iloc[i]))) if hl>0 else False
    is_strong_dn= (hl>0 and ((float(high.iloc[i]-close.iloc[i])/hl)>0.6 and float(close.iloc[i])<float(open_.iloc[i]))) if hl>0 else False
    break_dist=atr_i*p_break_mult
    break_up= (not math.isnan(res_level)) and float(close.iloc[i])>(res_level+break_dist)
    break_dn= (not math.isnan(sup_level)) and float(close.iloc[i])<(sup_level-break_dist)
    raw_bos_bull=break_up and is_strong_up and is_displace
    raw_bos_bear=break_dn and is_strong_dn and is_displace
    if raw_bos_bull:
        bos_bull_bar=i
        bos_bull_level=res_level
    if raw_bos_bear:
        bos_bear_bar=i
        bos_bear_level=sup_level
    bos_bull_valid=(i-bos_bull_bar)<=p_bos_max and (i-bos_bull_bar)>0
    bos_bear_valid=(i-bos_bear_bar)<=p_bos_max and (i-bos_bear_bar)>0
    retest_tol=atr_i*p_retest_mult
    retest_bull=bos_bull_valid and not math.isnan(bos_bull_level) and abs(float(low.iloc[i]-bos_bull_level))<=retest_tol and float(close.iloc[i])>bos_bull_level
    retest_bear=bos_bear_valid and not math.isnan(bos_bear_level) and abs(float(high.iloc[i]-bos_bear_level))<=retest_tol and float(close.iloc[i])<bos_bear_level
    bull_invalidated= not math.isnan(bos_bull_level) and float(close.iloc[i])<bos_bull_level
    bear_invalidated= not math.isnan(bos_bear_level) and float(close.iloc[i])>bos_bear_level
    if bull_invalidated:
        bos_bull_bar=-999
        bos_bull_level=float('nan')
    if bear_invalidated:
        bos_bear_bar=-999
        bos_bear_level=float('nan')
    score_trend=0.0
    if h4_regime==1 and float(close.iloc[i])>h4_fast: score_trend=p_w_trend
    elif h4_regime==-1 and float(close.iloc[i])<h4_fast: score_trend=p_w_trend
    elif h4_regime!=0: score_trend=p_w_trend*0.5
    score_struct=0.0
    if retest_bull or retest_bear: score_struct=p_w_struct
    elif bos_bull_valid or bos_bear_valid: score_struct=p_w_struct*0.7
    elif raw_bos_bull or raw_bos_bear: score_struct=p_w_struct*0.4
    score_mom=0.0
    if is_displace and (is_strong_up or is_strong_dn): score_mom=p_w_mom
    elif is_displace: score_mom=p_w_mom*0.5
    vol_ratio=1.0
    try:
        vs=float(vol_sma.iloc[i]) if not pd.isna(vol_sma.iloc[i]) else 0
        v=float(vol.iloc[i]) if not pd.isna(vol.iloc[i]) else 0
        vol_ratio=(v/vs) if vs>0 else 1.0
    except: vol_ratio=1.0
    score_vol=0.0
    if vol_ratio>=1.5: score_vol=p_w_vol
    elif vol_ratio>=1.2: score_vol=p_w_vol*0.7
    elif vol_ratio>=1.0: score_vol=p_w_vol*0.4
    score_liq=p_w_liq if vol_ok else p_w_liq*0.4
    total_score=score_trend+score_struct+score_mom+score_vol+score_liq
    bull_align=(h4_regime==1 and retest_bull and float(close.iloc[i])>h4_fast)
    bear_align=(h4_regime==-1 and retest_bear and float(close.iloc[i])<h4_fast)
    long_sig=bull_align and total_score>=p_thresh and vol_ok and (i-last_long>=3)
    short_sig=bear_align and total_score>=p_thresh and vol_ok and (i-last_short>=3)
    if long_sig: valid_buy+=1
    if short_sig: valid_sell+=1
    if trade_dir!=0:
        exit_tp=False
        exit_sl=False
        exit_reg=False
        exit_rec=False
        exit_time=(i-trade_bar)>=p_max_dur
        if trade_dir==1:
            if float(high.iloc[i])>=trade_tp: exit_tp=True
            if float(low.iloc[i])<=trade_sl: exit_sl=True
            if h4_regime==-1: exit_reg=True
            if bull_invalidated: exit_rec=True
        else:
            if float(low.iloc[i])<=trade_tp: exit_tp=True
            if float(high.iloc[i])>=trade_sl: exit_sl=True
            if h4_regime==1: exit_reg=True
            if bear_invalidated: exit_rec=True
        if exit_tp or exit_sl or exit_reg or exit_rec or exit_time:
            sl_dist=abs(trade_entry-trade_sl)
            r=(float(close.iloc[i])-trade_entry)/sl_dist if trade_dir==1 else (trade_entry-float(close.iloc[i]))/sl_dist
            if r>0:
                if trade_dir==1: w_b+=1
                else: w_s+=1
            else:
                if trade_dir==1: l_b+=1
                else: l_s+=1
            trades_log.append(r)
            trade_dir=0
            trade_entry=float('nan')
    if trade_dir==0:
        if long_sig:
            trade_dir=1
            trade_entry=float(close.iloc[i])
            trade_sl=trade_entry-(atr_i*p_risk_mult)
            trade_tp=trade_entry+(atr_i*p_reward_mult)
            trade_bar=i
            last_long=i
        elif short_sig:
            trade_dir=-1
            trade_entry=float(close.iloc[i])
            trade_sl=trade_entry+(atr_i*p_risk_mult)
            trade_tp=trade_entry-(atr_i*p_reward_mult)
            trade_bar=i
            last_short=i

trades=w_b+l_b+w_s+l_s
win=(w_b+w_s)*100.0/trades if trades else 0
pf=((w_b+w_s)*p_reward_mult)/((l_b+l_s)*p_risk_mult) if (l_b+l_s)>0 else 0
print(f"v20.3 (ชื่อเดิม: AG5 V20.3 Scoring/BOS/Retest M15) rows={len(df)} Valid Buy={valid_buy} Sell={valid_sell} Trades={trades} Win={win:.2f}% PF={pf:.2f} Buy {w_b}-{l_b} Sell {w_s}-{l_s}")
today=datetime.datetime.now().strftime("%Y-%m-%d")
path="HISTORY_AG5_V20_3.csv"
new=not os.path.exists(path)
with open(path,"a",newline="",encoding="utf-8") as f:
    import csv
    w=csv.writer(f)
    if new: w.writerow(["date","rows","valid_buy","valid_sell","trades","winrate","pf","code"])
    w.writerow([today,len(df),valid_buy,valid_sell,trades,f"{win:.2f}",f"{pf:.2f}","v20.3"])
