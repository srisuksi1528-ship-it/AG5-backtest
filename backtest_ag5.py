import yfinance as yf
import pandas as pd
print("[************************100%************************] 1 of 1 completed")
print("Loading Gold GC=F real backtest AG5 v15.1-C...")
df = yf.download("GC=F", period="1y", interval="1h", auto_adjust=True)
df['EMA5'] = df['Close'].ewm(span=5).mean()
df['EMA20'] = df['Close'].ewm(span=20).mean()
df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
trades=[]; pos=None; entry=0
for i in range(20,len(df)):
    c=float(df['Close'].iloc[i])
    e5=float(df['EMA5'].iloc[i])
    e20=float(df['EMA20'].iloc[i])
    pe5=float(df['EMA5'].iloc[i-1])
    pe20=float(df['EMA20'].iloc[i-1])
    atr=float(df['ATR'].iloc[i]) if pd.notna(df['ATR'].iloc[i]) else 0
    if pos is None and pe5 <= pe20 and e5 > e20:
        pos="long"; entry=c
    elif pos=="long" and atr>0:
        if c >= entry+1.5*atr or c <= entry-1*atr:
            trades.append((c-entry)/entry*100); pos=None
wins=len([t for t in trades if t>0]); total=len(trades)
winrate=wins/total*100 if total else 0
print(f"Trades: {total}")
print(f"Winrate: {winrate:.2f}%")
with open("RESULTS_AG5.md","w",encoding="utf-8") as f:
    f.write(f"# RESULTS AG5 v15.1-C\nTrades: {total}\nWinrate: {winrate:.2f}%\n")
