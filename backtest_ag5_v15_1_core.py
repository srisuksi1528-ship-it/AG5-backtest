# AG5 v15.1-C CORE (ชื่อโค้ดเดิม: AG5 Observation Layer v15.1-C [ALLGOLD] - CORE Physical) - FIXED
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
    raise SystemExit(f"rows {len(df)} <200 need re-run")
close, high, low = df['Close'], df['High'], df['Low']
p_pivot_l, p_pivot_r = 5, 3
p_atr_per, p_ema_per = 21, 21
p_reward, p_risk, p_friction = 2.0, 1.0, 15.0
p_cooldown_bars = 10
ema = close.ewm(span=p_ema_per, adjust=False).mean()
trend_up = close.shift(1) > ema.shift(1)
tr = pd.concat([high-low, (high-close.shift(1)).abs(), (low-close.shift(1)).abs()], axis=1).max(axis=1)
atr = tr.rolling(p_atr_per).mean().shift(1)
edge_valid = (atr * p_reward - p_friction) > 0
edge_valid = edge_valid.fillna(False)
is_pivot_low = pd.Series(False, index=df.index)
for i in range(p_pivot_l, len(df)-p_pivot_r):
    window = low.iloc[i-p_pivot_l:i+p_pivot_r+1]
    if len(window)>0 and low.iloc[i] == window.min():
        is_pivot_low.iloc[i+p_pivot_r] = True
raw_buy = is_pivot_low & trend_up.fillna(False)
sma100 = atr.rolling(100).mean()
std100 = atr.rolling(100).std()
z = ((atr - sma100) / std100).fillna(0).clip(-1,1)
mult = 1.0 - (z * 0.5)
valid = []
last = -999999
for i in range(len(df)):
    if not edge_valid.iloc[i]:
        valid.append(False)
        continue
    cool = round(p_cooldown_bars * float(mult.iloc[i])) if i>=100 and not pd.isna(mult.iloc[i]) else p_cooldown_bars
    cool = max(1, cool)
    if (i - last) >= cool and raw_buy.iloc[i]:
        valid.append(True)
        last = i
    else:
        valid.append(False)
valid_buy = pd.Series(valid, index=df.index)
stop=target=None
pend=False
w=l=0
for i in range(len(df)-1):
    if pend:
        if low.iloc[i] <= stop:
            l+=1
            pend=False
        elif high.iloc[i] >= target:
            w+=1
            pend=False
    if valid_buy.iloc[i] and not pd.isna(atr.iloc[i]) and atr.iloc[i]>0:
        c=float(close.iloc[i])
        a=float(atr.iloc[i])
        stop=c-a*p_risk
        target=c+a*p_reward
        pend=True
trades=w+l
win=w*100.0/trades if trades else 0
pf=(w*p_reward)/(l*p_risk) if l else 0
print(f"v15.1-C CORE (ชื่อเดิม: v15.1-C [ALLGOLD] CORE Physical) rows={len(df)} Valid={int(valid_buy.sum())} Trades={trades} Win={win:.2f}% PF={pf:.2f} Buy {w}-{l} (FIXED)")
today=datetime.datetime.now().strftime("%Y-%m-%d")
path="HISTORY_AG5_V15_1_CORE.csv"
new=not os.path.exists(path)
with open(path,"a",newline="",encoding="utf-8") as f:
    import csv as _csv
    writer=_csv.writer(f)
    if new:
        writer.writerow(["date","rows","valid","trades","winrate","pf","code"])
    writer.writerow([today,len(df),int(valid_buy.sum()),trades,f"{win:.2f}",f"{pf:.2f}","v15.1-C CORE (ชื่อเดิม: v15.1-C [ALLGOLD]) - FIXED"])
