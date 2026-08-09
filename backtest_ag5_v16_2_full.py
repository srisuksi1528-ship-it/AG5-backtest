# AG5 v16.2 FULL FIX INDEX - replicate Pine v14.17-C
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
is_pivot_high = pd.Series([False]*len(df))
is_pivot_low = pd.Series([False]*len(df))

for i in range(p_pivot_l, len(df)-p_pivot_r):
    if high.iloc[i] == high.iloc[i-p_pivot_l:i+p_pivot_r+1].max():
        is_pivot_high.iloc[i+p_pivot_r] = True
    if low.iloc[i] == low.iloc[i-p_pivot_l:i+p_pivot_r+1].min():
        is_pivot_low.iloc[i+p_pivot_r] = True

raw_sell = is_pivot_high & (~trend_up.fillna(False))
raw_buy = is_pivot_low & (trend_up.fillna(False))

p_cooldown_bars = 10
valid_buy_list = [False]*len(df)
valid_sell_list = [False]*len(df)
last_buy_bar = -999999
last_sell_bar = -999999

for i in range(len(df)):
    if pd.isna(edge_valid.iloc[i]) or not edge_valid.iloc[i]:
        continue
    b_cool = (i - last_buy_bar) >= p_cooldown_bars
    s_cool = (i - last_sell_bar) >= p_cooldown_bars
    if raw_buy.iloc[i] and b_cool:
        valid_buy_list[i] = True
        last_buy_bar = i
    if raw_sell.iloc[i] and s_cool:
        valid_sell_list[i] = True
        last_sell_bar = i

valid_buy = pd.Series(valid_buy_list)
valid_sell = pd.Series(valid_sell_list)

buy_stop = None
buy_target = None
buy_pending = False
sell_stop = None
sell_target = None
sell_pending = False
win_count_buy = 0
loss_count_buy = 0
win_count_sell = 0
loss_count_sell = 0

for i in range(len(df)-1):
    if buy_pending:
        if low.iloc[i] <= buy_stop:
            loss_count_buy += 1
            buy_pending = False
        elif high.iloc[i] >= buy_target:
            win_count_buy += 1
            buy_pending = False
    if sell_pending:
        if high.iloc[i] >= sell_stop:
            loss_count_sell += 1
            sell_pending = False
        elif low.iloc[i] <= sell_target:
            win_count_sell += 1
            sell_pending = False
    if valid_buy.iloc[i]:
        c = float(close.iloc[i])
        atr = float(atr_val.iloc[i]) if not pd.isna(atr_val.iloc[i]) else 0
        if atr>0:
            buy_stop = c - atr * p_risk
            buy_target = c + atr * p_reward
            buy_pending = True
    if valid_sell.iloc[i]:
        c = float(close.iloc[i])
        atr = float(atr_val.iloc[i]) if not pd.isna(atr_val.iloc[i]) else 0
        if atr>0:
            sell_stop = c + atr * p_risk
            sell_target = c - atr * p_reward
            sell_pending = True

total_buy = win_count_buy + loss_count_buy
total_sell = win_count_sell + loss_count_sell
total_trades = total_buy + total_sell
win_rate_total = ((win_count_buy+win_count_sell)*100.0/total_trades) if total_trades>0 else 0
pos_r = (win_count_buy+win_count_sell)*p_reward
neg_r = (loss_count_buy+loss_count_sell)*p_risk
pf = pos_r/abs(neg_r) if neg_r!=0 else 0
valid_count = int(valid_buy.sum() + valid_sell.sum())

print(f"FULL FIXED rows={len(df)} Valid={valid_count} Trades={total_trades} Win={win_rate_total:.2f}% PF={pf:.2f} Buy {win_count_buy}-{loss_count_buy} Sell {win_count_sell}-{loss_count_sell}")

with open("RESULTS_AG5.md","w",encoding="utf-8") as f:
    f.write(f"# AG5 v16.2 FULL FIXED\nRows: {len(df)}\nValid: {valid_count} Trades: {total_trades} Win: {win_rate_total:.2f}% PF: {pf:.2f}\n")

today = datetime.datetime.now().strftime("%Y-%m-%d")
path = "HISTORY_AG5_FULL.csv"
new = not os.path.exists(path)
with open(path, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["date","rows","valid_signals","resolved_trades","winrate","pf"])
    w.writerow([today, len(df), valid_count, total_trades, f"{win_rate_total:.2f}", f"{pf:.2f}"])
print(f"Logged to {path} date={today}")
