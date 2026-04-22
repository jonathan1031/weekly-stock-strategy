# ... (前面 get_signal 的邏輯不變) ...

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
        .container {{ background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .logic-card {{ background-color: #f8f9fa; border-left: 5px solid #212529; padding: 20px; margin-bottom: 30px; border-radius: 5px; }}
        .logic-title {{ font-weight: bold; color: #333; margin-bottom: 10px; }}
        .logic-item {{ font-size: 0.9rem; color: #555; margin-bottom: 5px; }}
        .table-dark {{ background-color: #212529; }}
        .badge-logic {{ font-size: 0.8rem; padding: 3px 8px; border-radius: 10px; background: #e9ecef; color: #495057; }}
    </style>
</head>
<body>
    <div class="container">
        <h2 class="mb-2">📈 策略監控面板</h2>
        <p class="text-muted mb-4">最後更新時間：{update_time}</p>

        <div class="logic-card">
            <div class="logic-title">🔍 策略邏輯說明</div>
            <div class="row">
                <div class="col-md-6">
                    <div class="logic-item"><strong>● 當前狀態：</strong> 
                        <span class="badge-logic">BUY</span> 趨勢向上(收盤>MA20且MA20上升) ＋ 動能翻正(MACD柱狀體由負轉正)。<br>
                        <span class="badge-logic">SELL</span> 收盤價跌破 MA10 (週線)，啟動移動鎖利。<br>
                        <span class="badge-logic">HOLD</span> 股價維持在 MA20 之上且未達賣出條件。
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="logic-item"><strong>● 建議停損：</strong> 以 2 倍 ATR (平均真實波幅) 計算之動態停損位。</div>
                    <div class="logic-item"><strong>● 風險空間：</strong> (現價 - 停損價) / 現價。代表目前進場預期承擔的原始風險。</div>
                    <div class="logic-item"><strong>● 進場評估：</strong> 風險空間 &le; 10% 顯示 <span class="text-success">✅風險適中</span>；&gt; 10% 顯示 <span class="text-danger">⚠️風險過高</span>。</div>
                </div>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-bordered align-middle">
                <thead class="table-dark text-center">
                    <tr>
                        <th>名稱</th>
                        <th>現價</th>
                        <th>當前狀態</th>
                        <th>建議停損</th>
                        <th>風險空間</th>
                        <th>進場評估</th>
                    </tr>
                </thead>
                <tbody class="text-center">
                    {html_rows}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)
