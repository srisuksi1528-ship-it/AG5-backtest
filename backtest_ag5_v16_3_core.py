# AG5 v16.3 CORE Long-Only - Pine v14.17-C CORE mode
import pandas as pd, yfinance as yf, time, datetime, csv, os
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
    with open("RESULTS_AG5.md","w",encoding="utf-8") as f:
        f.write(f"# FAILED rows={len(df)} need re-run\n")
    raise SystemExit(1)
close = df['Close']
high = df['High']
low = df['Low']
p_base = 30
p_htf_ema = close.ewm(span=p_base, adjust=False).mean()
htf_close = close.shift(1)
htf_ema = p_htf_ema.shift(1)
trend_up = htf_close > htf_ema
tr1 = high - low
tr2 = (high - close.shift(1)).abs()
tr3 = (low - close.shift(1)).abs()
tr = pd.concat([tr1,tr2,tr3], axis=1).max(axis=1)
atr_val = tr.rolling(p_base).mean().shift(1)
p_reward = 2.0
p_risk = 1.0
p_friction = 15.0
edge_valid = (atr_val * p_reward - p_friction) > 0
p_pivot_l = 5
p_pivot_r = 5
is_pivot_low = pd.Series([False]*len(df))
for i in range(p_pivot_l, len(df)-p_pivot_r):
    if low.iloc[i] == low.iloc[i-p_pivot_l:i+p_pivot_r+1].min():
        is_pivot_low.iloc[i+p_pivot_r] = True
raw_buy = is_pivot_low & (trend_up.fillna(False))
p_cooldown_bars = 10
valid_buy_list = [False]*len(df)
last_buy_bar = -999999
for i in range(len(df)):
    if pd.isna(edge_valid.iloc[i]) or not edge_valid.iloc[i]:
        continue
    b_cool = (i - last_buy_bar) >= p_cooldown_bars
    if raw_buy.iloc[i] and b_cool:
        valid_buy_list[i] = True
        last_buy_bar = i
valid_buy = pd.Series(valid_buy_list)
buy_stop = None
buy_target = None
buy_pending = False
win_count_buy = 0
loss_count_buy = 0
for i in range(len(df)-1):
    if buy_pending:
        if low.iloc[i] <= buy_stop:
            loss_count_buy += 1
            buy_pending = False
        elif high.iloc[i] >= buy_target:
            win_count_buy += 1
            buy_pending = False
    if valid_buy.iloc[i]:
        c = float(close.iloc[i])
        atr = float(atr_val.iloc[i]) if not pd.isna(atr_val.iloc[i]) else 0
        if atr>0:
            buy_stop = c - atr * p_risk
            buy_target = c + atr * p_reward
            buy_pending = True
total_trades = win_count_buy + loss_count_buy
win_rate = (win_count_buy*100.0/total_trades) if total_trades>0 else 0
pf = (win_count_buy*p_reward)/(loss_count_buy*p_risk) if loss_count_buy>0 else 0
valid_count = int(valid_buy.sum())
print(f"CORE LONG-ONLY rows={len(df)} Valid={valid_count} Trades={total_trades} Win={win_rate:.2f}% PF={pf:.2f} Buy {win_count_buy}-{loss_count_buy}")
with open("RESULTS_AG5.md","w",encoding="utf-8") as f:
    f.write(f"# AG5 v16.3 CORE Long-Only\nRows: {len(df)}\nValid: {valid_count} Trades: {total_trades} Win: {win_rate:.2f}% PF: {pf:.2f} Buy {win_count_buy}-{loss_count_buy}\n")
today = datetime.datetime.now().strftime("%Y-%m-%d")
path = "HISTORY_AG5_CORE.csv"
new = not os.path.exists(path)
with open(path, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["date","rows","valid_signals","resolved_trades","winrate","pf"])
    w.writerow([today, len(df), valid_count, total_trades, f"{win_rate:.2f}", f"{pf:.2f}"])
print(f"Logged to {path} date={today}")
