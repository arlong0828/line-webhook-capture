# LINE Webhook Capture

本機開發用的 LINE webhook 接收器，將原始事件寫入 JSONL，並另存最後一次來源 ID。

## 使用

```bash
cp .env.example .env
python line_webhook_capture.py
```

預設只綁定 `127.0.0.1:8787`。若要接受外部 webhook，請使用具備 HTTPS 與存取控制的反向代理或 tunnel。

## 隱私與安全

- `data/` 與 `.env` 不會提交至 Git。
- Webhook 事件可能含 LINE User ID、群組 ID、訊息文字與簽章，屬敏感資料。
- 本工具只適合開發除錯；正式環境應驗證 `x-line-signature`，並設定資料保留期限。
- `Authorization` 與 `Cookie` header 會在紀錄中遮罩。
