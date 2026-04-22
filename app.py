import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 自定義中文名稱對照表 ---
STOCK_NAMES = {
    "0050.TW": "元大台灣50", "2330.TW": "台積電", "006208.TW": "富邦台50",
    "2317.TW": "鴻海", "2412.TW": "中華電", "2308.TW": "台達電",
    "00850.TW": "元大臺灣ESG永續", "2454.TW": "聯發科", "1215.TW": "卜蜂",
    "0052.TW": "富邦科技", "2885.TW": "元大金", "1737.TW": "臺鹽",
    "2002.TW": "中鋼", "2345.TW": "智邦", "3380.TW": "明泰",
    "2353.TW": "宏碁", "3714.TW": "富采", "2357.TW": "華碩", "4938.TW": "和碩"
}

def get_signal(ticker):
    ticker_full = ticker if ticker.endswith(('.TW', '.TWO')) else f"{ticker}.TW"
    stock_name = STOCK_NAMES.get(ticker_full, ticker)
    
    try:
        df = yf.download(ticker_full, period="2y", interval="1wk", progress=False, auto_adjust=True)
        if df.empty or len(df) < 20: return None

        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        # 指標計算
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['Hist'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
        
        # ATR 停損
        hl = df['High'] - df['Low']
        hcp = np.abs(df['High'] - df['Close'].shift())
        lcp = np.abs(df['Low'] - df['Close'].shift())
        df['ATR'] = pd.concat([hl, hcp, lcp], axis=1).max(axis=1).rolling(window=14).mean()

        curr = df.iloc[-1]
        prev = df.iloc[-2]
        price = float(curr['Close'])
        stop_price = price - (2 * float(curr['ATR']))
        risk_pct = ((price - stop_price) / price) * 100

        # 邏輯
        trend_ok = price > curr['MA20'] and curr['MA20'] > prev['MA20']
        macd_cross_up = curr['Hist'] > 0 and prev['Hist'] <= 0
        exit_signal = price < curr['MA10']
        
        status = "觀察中"
        status_color = "table-light"
        if trend_ok and macd_cross_up: 
            status = "★ 買入點 (BUY)"
            status_color = "table-danger"
        elif exit_signal: 
            status = "✘ 賣出點 (SELL)"
            status_color = "table-success"
        elif price > curr['MA20']: 
            status = "持股續抱 (HOLD)"
            status_color = "table-warning"
        
        entry_advice = "✅ 風險適中" if risk_pct <= 10 else "⚠️ 風險過高"
        
        return {
            "名稱": stock_name, "現價": f"{price:.2f}", "當前狀態": status,
            "建議停損": f"{stop_price:.2f}", "風險空間": f"{risk_pct:.1f}%",
            "進場評估": entry_advice, "CSS": status_color
        }
    except: return None

# 執行所有標的
tickers = list(STOCK_NAMES.keys())
results = [get_signal(t) for t in tickers if get_signal(t) is not None]
df_final = pd.DataFrame(results)

# 產生 HTML
update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
html_rows = ""
for _, row in df_final.iterrows():
    html_rows += f"""
    <tr class="{row['CSS']}">
        <td>{row['名稱']}</td><td>{row['現價']}</td><td>{row['當前狀態']}</td>
        <td>{row['建議停損']}</td><td>{row['風險空間']}</td><td>{row['進場評估']}</td>
    </tr>
    """

html_template = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>策略監控面板</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style> body {{ padding: 20px; background-color: #f8f9fa; }} .container {{ background: white; padding: 30px; border-radius: 15px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }} </style>
</head>
<body>
    <div class="container">
        <h2 class="mb-4">📈 策略監控面板</h2>
        <p class="text-muted">最後更新時間：{update_time}</p>
        <table class="table table-bordered align-middle">
            <thead class="table-dark">
                <tr><th>名稱</th><th>現價</th><th>當前狀態</th><th>建議停損</th><th>風險空間</th><th>進場評估</th></tr>
            </thead>
            <tbody>{html_rows}</tbody>
        </table>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)
