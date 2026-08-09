# AG5 v16.0 INSTITUTIONAL (ชื่อโค้ดเดิม: AG5 Institutional Engine v16 - BOS + ADX + Volatility Gate)
import pandas as pd, yfinance as yf, time, datetime, os
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

close, high, low, open_ = df['Close'], df['High'], df['Low'], df['Open']
# PARAMS v16
p_pivot_l, p_pivot_r = 5, 5
p_ema, p_atr, p_adx = 50, 14, 14
p_reward, p_risk = 2.0, 1.0

# ATR
tr1 = high-low
tr2 = (high-close.shift(1)).abs()
tr3 = (low-close.shift(1)).abs()
tr = pd.concat([tr1,tr2,tr3], axis=1).max(axis=1)
atr = tr.rolling(p_atr).mean()
atr_val = atr.copy()

# EMA TREND + SLOPE
ema_trend = close.ewm(span=p_ema, adjust=False).mean()
ema_slope = ((ema_trend - ema_trend.shift(1)) / ema_trend.shift(1).replace(0,1) * 100).fillna(0)

# DMI ADX (Wilder)
up_move = high.diff()
down_move = -low.diff()
plus_dm = pd.Series(0.0, index=df.index)
minus_dm = pd.Series(0.0, index=df.index)
plus_dm[(up_move > down_move) & (up_move > 0)] = up_move[(up_move > down_move) & (up_move > 0)]
minus_dm[(down_move > up_move) & (down_move > 0)] = down_move[(down_move > up_move) & (down_move > 0)]
# Wilder smoothing RMA = ewm(alpha=1/n)
tr_smooth = tr.ewm(alpha=1/p_adx, adjust=False).mean()
plus_dm_s = plus_dm.ewm(alpha=1/p_adx, adjust=False).mean()
minus_dm_s = minus_dm.ewm(alpha=1/p_adx, adjust=False).mean()
diplus = 100 * plus_dm_s / tr_smooth
diminus = 100 * minus_dm_s / tr_smooth
dx = (100 * (diplus - diminus).abs() / (diplus + diminus).replace(0,1)).fillna(0)
adx_val = dx.ewm(alpha=1/p_adx, adjust=False).mean()

is_trending = (adx_val > 20) & (ema_slope.abs() > 0.01)
trend_up = (close > ema_trend) & is_trending & (diplus > diminus)
trend_dn = (close < ema_trend) & is_trending & (diminus > diplus)

atr_sma50 = atr.rolling(50).mean()
volatility_ok = atr > (atr_sma50 * 0.7)
volatility_ok = volatility_ok.fillna(True)

# PIVOT HIGH/LOW
ph = pd.Series(float('nan'), index=df.index)
pl = pd.Series(float('nan'), index=df.index)
for i in range(p_pivot_l, len(df)-p_pivot_r):
    if high.iloc[i] == high.iloc[i-p_pivot_l:i+p_pivot_r+1].max():
        ph.iloc[i+p_pivot_r] = high.iloc[i]
    if low.iloc[i] == low.iloc[i-p_pivot_l:i+p_pivot_r+1].min():
        pl.iloc[i+p_pivot_r] = low.iloc[i]

res_arr, sup_arr = [], []
res_level_s, sup_level_s = pd.Series(float('nan'), index=df.index), pd.Series(float('nan'), index=df.index)
for i in range(len(df)):
    if not pd.isna(ph.iloc[i]):
        res_arr.insert(0, ph.iloc[i])
        if len(res_arr) > 3: res_arr.pop()
    if not pd.isna(pl.iloc[i]):
        sup_arr.insert(0, pl.iloc[i])
        if len(sup_arr) > 3: sup_arr.pop()
    if len(res_arr) > 0: res_level_s.iloc[i] = res_arr[0]
    if len(sup_arr) > 0: sup_level_s.iloc[i] = sup_arr[0]

# EXECUTION GATES
body_size = (close - open_).abs()
is_displace = body_size > (atr_val * 0.5)
range_ = (high - low).replace(0,1)
is_strong_up = ((close - low) / range_ > 0.6) & (close > open_)
is_strong_dn = ((high - close) / range_ > 0.6) & (close < open_)

min_dist = 0.1 # mintick*5 approx for GC=F daily
break_up = close > (res_level_s + min_dist)
break_dn = close < (sup_level_s - min_dist)

raw_bos_bull = break_up & is_strong_up & is_displace
raw_bos_bear = break_dn & is_strong_dn & is_displace

# BOS Validity Window 3 bars + Struct Changed
last_bos_buy, last_bos_sel = -99, -99
locked_res, locked_sup = float('nan'), float('nan')
valid_buy_list, valid_sell_list = [], []
import math
for i in range(len(df)):
    if raw_bos_bull.iloc[i]: last_bos_buy = i
    if raw_bos_bear.iloc[i]: last_bos_sel = i
    bos_valid_buy = (i - last_bos_buy) <= 3
    bos_valid_sel = (i - last_bos_sel) <= 3

    res = res_level_s.iloc[i]
    sup = sup_level_s.iloc[i]
    struct_changed_buy = False if pd.isna(res) else (res!= locked_res or (isinstance(locked_res,float) and math.isnan(locked_res)))
    struct_changed_sel = False if pd.isna(sup) else (sup!= locked_sup or (isinstance(locked_sup,float) and math.isnan(locked_sup)))

    vb = bool(raw_bos_bull.iloc[i] and bos_valid_buy and trend_up.iloc[i] and volatility_ok.iloc[i] and struct_changed_buy)
    vs = bool(raw_bos_bear.iloc[i] and bos_valid_sel and trend_dn.iloc[i] and volatility_ok.iloc[i] and struct_changed_sel)

    if vb: locked_res = res
    if vs: locked_sup = sup

    valid_buy_list.append(vb)
    valid_sell_list.append(vs)

valid_buy = pd.Series(valid_buy_list)
valid_sell = pd.Series(valid_sell_list)

# BACKTEST RR BOTH SIDE
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
        if valid_buy.iloc[i] and not pd.isna(atr.iloc[i]) and atr.iloc[i]>0:
            c=float(close.iloc[i]); a=float(atr.iloc[i])
            stop=c-a*p_risk; target=c+a*p_reward; side='BUY'; pend=True
        elif valid_sell.iloc[i] and not pd.isna(atr.iloc[i]) and atr.iloc[i]>0:
            c=float(close.iloc[i]); a=float(atr.iloc[i])
            stop=c+a*p_risk; target=c-a*p_reward; side='SELL'; pend=True

trades=w_b+l_b+w_s+l_s
win=(w_b+w_s)*100.0/trades if trades else 0
pf=((w_b+w_s)*p_reward)/((l_b+l_s)*p_risk) if (l_b+l_s)>0 else 0
print(f"v16 INSTITUTIONAL (ชื่อเดิม: AG5 Institutional Engine v16) rows={len(df)} Valid Buy={int(valid_buy.sum())} Sell={int(valid_sell.sum())} Trades={trades} Win={win:.2f}% PF={pf:.2f} Buy {w_b}-{l_b} Sell {w_s}-{l_s}")

today=datetime.datetime.now().strftime("%Y-%m-%d")
path="HISTORY_AG5_V16_0.csv"
new=not os.path.exists(path)
with open(path,"a",newline="",encoding="utf-8") as f:
    import csv
    w=csv.writer(f)
    if new: w.writerow(["date","rows","valid_buy","valid_sell","trades","winrate","pf","code"])
    w.writerow([today,len(df),int(valid_buy.sum()),int(valid_sell.sum()),trades,f"{win:.2f}",f"{pf:.2f}","v16 INSTITUTIONAL (v16)"])
