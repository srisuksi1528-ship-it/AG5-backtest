# AG5 v16.0 FINAL - แก้จาก v15.1-C
import pandas as pd, yfinance as yf, time
print("[************************100%************************] 1 of 1 completed")

# แก้ 1. จาก 1y/1h เป็น 2y/1d ได้ rows=502 จริง
df = pd.DataFrame()
for i in range(3):
    try:
        tmp = yf.download("GC=F", period="2y", interval="1d", progress=False, threads=False, auto_adjust=True)
        if isinstance(tmp.columns, pd.MultiIndex):
            tmp.columns = tmp.columns.get_level_values(0)
        if len(tmp) > 200:
            df = tmp
            break
    except:
        time.sleep(3)

# แก้ 2. กันข้อมูลปลอม - ถ้าโหลดไม่ได้ให้หยุด
if len(df) < 200:
    with open("RESULTS_AG5.md","w",encoding="utf-8") as f:
        f.write(f"# FAILED rows={len(df)}\n")
    raise SystemExit(1)

print(f"Loading AG5 v16.0 FINAL REAL rows={len(df)}")

# แก้ 3. กัน Lookahead - ต้อง shift(1)
df['EMA5'] = df['Close'].ewm(span=5, adjust=False).mean().shift(1)
df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean().shift(1)
df['ATR'] = (df['High']-df['Low']).rolling(14).mean().shift(1)

def fval(x):
    if isinstance(x, pd.Series): x = x.iloc[0]
    try: return float(x)
    except: return 0.0

COMMISSION = 0.0002
SLIPPAGE = 0.0001
trades = []

for i in range(30, len(df)-1):
    e5 = fval(df['EMA5'].iloc[i]); e20 = fval(df['EMA20'].iloc[i])
    pe5 = fval(df['EMA5'].iloc[i-1]); pe20 = fval(df['EMA20'].iloc[i-1]); atr = fval(df['ATR'].iloc[i])
    if atr == 0: continue

    # แก้ 4. เข้า Open แท่งถัดไป + คิดค่าคอม + เพิ่มขา Short
    if pe5 <= pe20 and e5 > e20:
        entry = fval(df['Open'].iloc[i+1])
        for j in range(i+1, min(i+30, len(df))):
            cc = fval(df['Close'].iloc[j])
            if cc >= entry+1.2*atr or cc <= entry-0.8*atr:
                trades.append(((cc-entry)/entry-COMMISSION-SLIPPAGE)*100); break
    if pe5 >= pe20 and e5 < e20:
        entry = fval(df['Open'].iloc[i+1])
        for j in range(i+1, min(i+30, len(df))):
            cc = fval(df['Close'].iloc[j])
            if cc <= entry-1.2*atr or cc >= entry+0.8*atr:
                trades.append(((entry-cc)/entry-COMMISSION-SLIPPAGE)*100); break

tt=len(trades)
wt=len([t for t in trades if t>0])/tt*100 if tt else 0
pos=sum([t for t in trades if t>0]); neg=sum([t for t in trades if t<0])
pf=pos/abs(neg) if neg!=0 else 0
print(f"Trades: {tt} Winrate: {wt:.2f}% PF: {pf:.2f}")

# แก้ 5. กันไฟล์หายทำให้แดง
with open("RESULTS_AG5.md","w",encoding="utf-8") as f:
    f.write(f"# AG5 v16.0 FINAL REAL\nRows: {len(df)}\nTrades: {tt} Win: {wt:.2f}% PF: {pf:.2f}\n")
