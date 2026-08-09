# AG5 v16.0-C-LITE (ชื่อโค้ดเดิม: AG5 Observation Layer v16.0-C-LITE [ALLGOLD] - BOS/CHoCH)
import pandas as pd, yfinance as yf, time, datetime, os, math
print("[************************100%************************] 1 of 1 completed")
df = pd.DataFrame()
for i in range(3):
    try:
        tmp = yf.download("GC=F", period="2y", interval="1d", progress=False, threads=False, auto_adjust=True)
        if isinstance(tmp.columns, pd.MultiIndex):
            tmp.columns = tmp.columns.get_level_values(0)
        if len(tmp) > 200:
            df = tmp.reset_index(drop=True)
            break
    except:
        time.sleep(3)
if len(df) < 200:
    raise SystemExit(f"rows {len(df)} <200")

close, high, low = df['Close'], df['High'], df['Low']
p_pivot_l, p_pivot_r = 5, 5
p_base = 30
p_reward, p_risk, p_friction = 2.0, 1.0, 15.0
p_cooldown_bars = 10

# HTF Trend D (for daily data: close[1] > EMA30[1])
ema_base = close.ewm(span=p_base, adjust=False).mean()
htf_close = close.shift(1)
htf_ema = ema_base.shift(1)
trend_up = (htf_close > htf_ema).fillna(False)

# ATR
tr1 = high-low
tr2 = (high-close.shift(1)).abs()
tr3 = (low-close.shift(1)).abs()
tr = pd.concat([tr1,tr2,tr3], axis=1).max(axis=1)
atr_val = tr.rolling(p_base).mean()
edge_valid = (atr_val * p_reward - p_friction) > 0
edge_valid = edge_valid.fillna(False)

# PIVOT -> SWING LEVELS
ph = pd.Series(float('nan'), index=df.index)
pl = pd.Series(float('nan'), index=df.index)
for i in range(p_pivot_l, len(df)-p_pivot_r):
    win_h = high.iloc[i-p_pivot_l:i+p_pivot_r+1]
    win_l = low.iloc[i-p_pivot_l:i+p_pivot_r+1]
    if len(win_h)>0 and high.iloc[i] == win_h.max():
        ph.iloc[i+p_pivot_r] = high.iloc[i]
    if len(win_l)>0 and low.iloc[i] == win_l.min():
        pl.iloc[i+p_pivot_r] = low.iloc[i]

last_swing_high = float('nan')
last_swing_low = float('nan')
last_buy_bar = -999999
last_sell_bar = -999999
valid_buy_list=[]
valid_sell_list=[]

for i in range(len(df)):
    bull_choch = False
    bear_choch = False
    if i>0 and not pd.isna(last_swing_high):
        if close.iloc[i-1] <= last_swing_high and close.iloc[i] > last_swing_high:
            bull_choch = True
    if i>0 and not pd.isna(last_swing_low):
        if close.iloc[i-1] >= last_swing_low and close.iloc[i] < last_swing_low:
            bear_choch = True

    raw_buy = bull_choch and bool(trend_up.iloc[i])
    raw_sell = bear_choch and not bool(trend_up.iloc[i])

    buy_cool_ok = (i - last_buy_bar) >= p_cooldown_bars
    sell_cool_ok = (i - last_sell_bar) >= p_cooldown_bars

    vb = raw_buy and bool(edge_valid.iloc[i]) and buy_cool_ok
    vs = raw_sell and bool(edge_valid.iloc[i]) and sell_cool_ok

    if vb: last_buy_bar = i
    if vs: last_sell_bar = i

    valid_buy_list.append(vb)
    valid_sell_list.append(vs)

    # update levels AFTER check (same as Pine)
    if not pd.isna(ph.iloc[i]):
        last_swing_high = float(ph.iloc[i])
    if not pd.isna(pl.iloc[i]):
        last_swing_low = float(pl.iloc[i])

valid_buy = pd.Series(valid_buy_list)
valid_sell = pd.Series(valid_sell_list)

# BACKTEST RR
stop=target=None
side=None
pend=False
w_b=l_b=w_s=l_s=0
for i in range(len(df)-1):
    if pend:
        if side=='BUY':
            if low.iloc[i] <= stop: l_b+=1; pend=False
            elif high.iloc[i] >= target: w_b+=1; pend=False
        else:
            if high.iloc[i] >= stop: l_s+=1; pend=False
            elif low.iloc[i] <= target: w_s+=1; pend=False
    if not pend:
        if valid_buy_list[i] and not pd.isna(atr_val.iloc[i]) and atr_val.iloc[i]>0:
            c=float(close.iloc[i]); a=float(atr_val.iloc[i])
            stop=c-a*p_risk; target=c+a*p_reward; side='BUY'; pend=True
        elif valid_sell_list[i] and not pd.isna(atr_val.iloc[i]) and atr_val.iloc[i]>0:
            c=float(close.iloc[i]); a=float(atr_val.iloc[i])
            stop=c+a*p_risk; target=c-a*p_reward; side='SELL'; pend=True

trades=w_b+l_b+w_s+l_s
win=(w_b+w_s)*100.0/trades if trades else 0
pf=((w_b+w_s)*p_reward)/((l_b+l_s)*p_risk) if (l_b+l_s)>0 else 0
print(f"v16.0-C-LITE (ชื่อเดิม: v16.0-C-LITE [ALLGOLD] BOS/CHoCH) rows={len(df)} Valid Buy={int(valid_buy.sum())} Sell={int(valid_sell.sum())} Trades={trades} Win={win:.2f}% PF={pf:.2f} Buy {w_b}-{l_b} Sell {w_s}-{l_s}")

today=datetime.datetime.now().strftime("%Y-%m-%d")
path="HISTORY_AG5_V16_0_C_LITE.csv"
new=not os.path.exists(path)
with open(path,"a",newline="",encoding="utf-8") as f:
    import csv
    w=csv.writer(f)
    if new: w.writerow(["date","rows","valid_buy","valid_sell","trades","winrate","pf","code"])
    w.writerow([today,len(df),int(valid_buy.sum()),int(valid_sell.sum()),trades,f"{win:.2f}",f"{pf:.2f}","v16.0-C-LITE"])
