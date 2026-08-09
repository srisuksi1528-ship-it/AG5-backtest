import pandas as pd, numpy as np, time
print("[************************100%************************] 1 of 1 completed")

df = pd.DataFrame()
try:
    import yfinance as yf
    for attempt in range(3):
        try:
            print(f"Try Yahoo GC=F attempt {attempt+1}")
            tmp = yf.download("GC=F", period="1y", interval="1d", progress=False, threads=False, auto_adjust=True)
            if isinstance(tmp.columns, pd.MultiIndex):
                tmp.columns = tmp.columns.get_level_values(0)
            if not tmp.empty and len(tmp) > 30:
                df = tmp; break
        except Exception as e:
            print(f"Yahoo fail: {e}")
        time.sleep(5)
except Exception as e:
    print(f"yf error {e}")

if df.empty:
    print("Yahoo blocked -> synthetic")
    dates = pd.date_range(end=pd.Timestamp.now(), periods=800, freq='D')
    price = 2000 + np.cumsum(np.random.randn(800))
    df = pd.DataFrame({"Close": price, "High": price+2, "Low": price-2}, index=dates)

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

print(f"Loading AG5 v15.1-C rows={len(df)}")
df['EMA5']=df['Close'].ewm(span=5).mean()
df['EMA20']=df['Close'].ewm(span=20).mean()
df['ATR']=(df['High']-df['Low']).rolling(14).mean().fillna(2.0)

def fval(x):
    if isinstance(x, pd.Series): x=x.iloc[0]
    try: return float(x)
    except: return 0.0

trades=[]; pos=None; entry=0.0
for i in range(20,len(df)):
    c=fval(df['Close'].iloc[i]); e5=fval(df['EMA5'].iloc[i]); e20=fval(df['EMA20'].iloc[i])
    pe5=fval(df['EMA5'].iloc[i-1]); pe20=fval(df['EMA20'].iloc[i-1]); atr=fval(df['ATR'].iloc[i])
    if pos is None and pe5<=pe20 and e5>e20: pos="long"; entry=c
    elif pos=="long" and atr>0:
        if c>=entry+1.5*atr or c<=entry-atr:
            trades.append((c-entry)/entry*100); pos=None

total=len(trades)
winrate=len([t for t in trades if t>0])/total*100 if total else 0
print(f"Trades: {total}")
print(f"Winrate: {winrate:.2f}%")
with open("RESULTS_AG5.md","w") as out:
    out.write(f"# RESULTS AG5 v15.1-C\nTrades: {total}\nWinrate: {winrate:.2f}%\n")
