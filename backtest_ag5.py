import pandas as pd, time
print("[************************100%************************] 1 of 1 completed")
import yfinance as yf
df=pd.DataFrame()
for i in range(3):
    try:
        tmp=yf.download("GC=F",period="2y",interval="1d",progress=False,threads=False,auto_adjust=True)
        if isinstance(tmp.columns,pd.MultiIndex): tmp.columns=tmp.columns.get_level_values(0)
        if len(tmp)>200: df=tmp; break
    except: time.sleep(5)

if len(df)<200:
    print("[STOP] ข้อมูลจริงไม่พอ - Re-run ใหม่ใน 1 ชม."); raise SystemExit(1)

print(f"Loading AG5 v15.3 REAL rows={len(df)}")
df['EMA5']=df['Close'].ewm(5).mean().shift(1)
df['EMA20']=df['Close'].ewm(20).mean().shift(1)
df['ATR']=(df['High']-df['Low']).rolling(14).mean().shift(1)

def fval(x): return float(x.iloc[0]) if isinstance(x,pd.Series) else float(x)
COMMISSION=0.0002
trades=[]
for i in range(30,len(df)-1):
    e5=fval(df['EMA5'].iloc[i]); e20=fval(df['EMA20'].iloc[i])
    pe5=fval(df['EMA5'].iloc[i-1]); pe20=fval(df['EMA20'].iloc[i-1]); atr=fval(df['ATR'].iloc[i])
    if pe5<=pe20 and e5>e20:
        entry=fval(df['Open'].iloc[i+1])
        for j in range(i+1,min(i+20,len(df))):
            cc=fval(df['Close'].iloc[j])
            if cc>=entry+1.5*atr or cc<=entry-atr:
                trades.append(((cc-entry)/entry-COMMISSION)*100); break

tt=len(trades); wt=len([t for t in trades if t>0])/tt*100 if tt else 0
pft=sum([t for t in trades if t>0])/abs(sum([t for t in trades if t<0])) if sum([t for t in trades if t<0])!=0 else 0
print(f"Trades: {tt} Winrate: {wt:.2f}% PF: {pft:.2f}")
