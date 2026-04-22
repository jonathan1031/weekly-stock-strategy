import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. 自定義中文名稱對照表 ---
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
        # 下載週線數據 (2年期)
        df = yf.download(ticker_full, period="2y", interval="1wk", progress=False, auto_adjust=True, timeout=15)
        
        if df.empty or len(df) < 20:
            print(f"警告: {ticker_full} 數據不足")
            return None

        # 處理 MultiIndex (Yahoo Finance API 新版格式相容)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 指標計算: MA20, MA10
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        
        # MACD 計算
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['Hist'] = df['MACD'] - df['Signal']
        
        # ATR 停損計算 (2倍ATR)
        hl = df['High'] - df['Low']
        hcp = np.abs(df['High'] - df['Close'].shift())
        lcp = np.abs(df['Low'] - df['Close'].shift())
        df['TR'] = pd.concat([hl, hcp, lcp], axis=1).max(axis=1)
        df['ATR'] = df['TR'].rolling(window=14).mean()

        curr = df.iloc[-1]
        prev = df.iloc[-2]
        price = float(curr['Close'])
        stop_price = price - (2 * float(curr['ATR']))
        risk_pct = ((price - stop_price) / price) * 100

        # 策略狀態判斷
        trend_ok = price > curr['MA20'] and curr['MA20'] > prev['MA20']
        macd_cross_up = curr['Hist'] > 0 and prev['Hist'] <= 0
        exit_signal = price < curr['MA10']
        
        status = "觀察中"
        status_color = "table-light"
        
        if trend_ok and macd_cross_up: 
            status = "★ 買入點 (BUY)"
            status_color = "table-danger" # 紅色
        elif exit_signal: 
            status = "✘ 賣出點 (SELL)"
            status_color = "table-success" # 綠色
        elif price > curr['MA20']: 
            status = "持股續抱 (HOLD)"
            status_color = "table-warning" # 黃色
        
        entry_advice = "✅ 風險適中" if risk_pct <= 10 else "⚠️ 風險過高"
        if status not in ["★ 買入點 (BUY)", "持股續抱 (HOLD)"]:
            entry_advice = "-"

        return {
            "名稱": stock_name,
            "股號": ticker_full,
            "現價": f"{price:.2f}",
            "當前狀態": status,
            "建議停損": f"{stop_price:.2f}",
            "風險空間": f"{risk_pct:.1f}%",
            "進場評估": entry_advice,
            "CSS": status_color
        }
    except Exception as e:
        print(f"錯誤: 無法處理 {ticker_full}, 原因: {e}")
        return None

# --- 2. 執行資料抓取與處理 ---
tickers = list(STOCK_NAMES.keys())
results = []
for t in tickers:
    res = get_signal(t)
    if res:
        results.append(res)

df_final = pd.DataFrame(results)

# --- 3. 先定義時間與表格內容 (修正時區為 GMT+8) ---
from datetime import datetime, timedelta, timezone

# 建立 GMT+8 時區
tz_taiwan = timezone(timedelta(hours=8))
# 取得目前 GMT+8 的時間
update_time = datetime.now(tz_taiwan).strftime("%Y-%m-%d %H:%M:%S")


html_rows = ""
for _, row in df_final.iterrows():
    html_rows += f"""
    <tr class="{row['CSS']}">
        <td class="fw-bold">{row['名稱']}</td>
        <td>{row['股號']}</td>
        <td>{row['現價']}</td>
        <td class="fw-bold">{row['當前狀態']}</td>
        <td>{row['建議停損']}</td>
        <td>{row['風險空間']}</td>
        <td>{row['進場評估']}</td>
    </tr>
    """

# --- 4. 定義 HTML 模板 (最後才定義，確保能讀取到 update_time) ---
html_template = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>策略監控面板</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ padding: 20px; background-color: #f0f2f5; font-family: "Microsoft JhengHei", sans-serif; }}
        .container-main {{ background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .logic-card {{ background-color: #f8f9fa; border-left: 5px solid #333; padding: 20px; margin-bottom: 25px; border-radius: 8px; }}
        .logic-title {{ font-weight: bold; color: #333; margin-bottom: 8px; font-size: 1.1rem; }}
        .logic-item {{ font-size: 0.9rem; color: #555; line-height: 1.6; }}
        .table thead {{ background-color: #212529; color: white; }}
        .badge-logic {{ font-size: 0.75rem; padding: 2px 6px; border-radius: 5px; background: #dee2e6; color: #495057; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container-main container">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="m-0">📈 策略監控面板</h2>
            <span class="text-muted">🕒 更新時間：{update_time}</span>
        </div>

        <div class="logic-card shadow-sm">
            <div class="logic-title">🔍 策略邏輯說明</div>
            <div class="row">
                <div class="col-md-6">
                    <div class="logic-item"><strong>● 當前狀態：</strong><br>
                        <span class="badge-logic">BUY</span> 趨勢向上(收盤>MA20且MA20上升) ＋ 動能翻正(MACD柱狀體由負轉正)。<br>
                        <span class="badge-logic">SELL</span> 收盤價跌破 MA10 (週線)，啟動移動鎖利。<br>
                        <span class="badge-logic">HOLD</span> 股價維持在 MA20 之上且未達賣出條件。
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="logic-item"><strong>● 建議停損：</strong> 以 2 倍 ATR (平均真實波幅) 計算之動態移動停損價位。</div>
                    <div class="logic-item"><strong>● 風險空間：</strong> (現價 - 停損價) / 現價。代表目前進場預期承擔的原始風險。</div>
                    <div class="logic-item"><strong>● 進場評估：</strong> 風險空間 &le; 10% 顯示 <span class="text-success fw-bold">✅風險適中</span>；&gt; 10% 顯示 <span class="text-danger fw-bold">⚠️風險過高</span>。</div>
                </div>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover table-bordered align-middle text-center">
                <thead>
                    <tr>
                        <th>名稱</th>
                        <th>股號</th>
                        <th>現價</th>
                        <th>當前狀態</th>
                        <th>建議停損</th>
                        <th>風險空間</th>
                        <th>進場評估</th>
                    </tr>
                </thead>
                <tbody>
                    {html_rows}
                </tbody>
            </table>
        </div>
        <div class="mt-3 text-end text-muted" style="font-size: 0.8rem;">
            * 本工具僅供策略參考，不構成任何投資建議。資料來源：Yahoo Finance
        </div>
    </div>
</body>
</html>
"""

# --- 5. 寫入檔案 ---
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print("index.html 產生成功！")
