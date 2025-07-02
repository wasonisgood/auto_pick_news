# 🚀 部署檢查清單

> 按照此清單逐步完成部署，確保服務正常運作

## 📋 部署前準備

### ✅ 檔案準備
- [ ] `netlify/functions/analyze_news.py` - 主要 Function 程式
- [ ] `.github/workflows/daily-news-analysis.yml` - GitHub Actions 工作流程
- [ ] `netlify.toml` - Netlify 配置檔案
- [ ] `requirements.txt` - Python 依賴套件
- [ ] `public/index.html` - 測試頁面
- [ ] `local_test.py` - 本地測試腳本
- [ ] `README.md` - 部署說明文檔

### ✅ 本地測試
```bash
# 執行本地測試
python local_test.py
```
- [ ] 環境變數檢查通過
- [ ] 套件導入成功
- [ ] Function 執行成功
- [ ] 能正常選出 5 則新聞
- [ ] 資料庫儲存正常

## 🌐 Netlify 部署

### ✅ 建立 Netlify 站點
1. [ ] 前往 [netlify.com](https://netlify.com) 並登入
2. [ ] 點擊 "New site from Git"
3. [ ] 連接 GitHub 儲存庫
4. [ ] 設定構建參數:
   - Build command: (留空)
   - Publish directory: `public`
   - Functions directory: `netlify/functions`
5. [ ] 點擊 "Deploy site"

### ✅ 設定環境變數
前往 `Site settings → Environment variables` 並加入:
- [ ] `OPENAI_API_KEY` = `sk-your-api-key`
- [ ] `SUPABASE_URL` = `https://your-project.supabase.co`
- [ ] `SUPABASE_KEY` = `your-anon-key`

### ✅ 測試部署
- [ ] Function 部署成功 (無錯誤訊息)
- [ ] 訪問測試頁面: `https://your-site.netlify.app`
- [ ] 手動觸發分析按鈕能正常運作
- [ ] 查看 Function 日誌無錯誤

## 🐙 GitHub Actions 設定

### ✅ 設定 Repository Secrets
前往 `Settings → Secrets and variables → Actions`:
- [ ] `NETLIFY_FUNCTION_URL` = `https://your-site.netlify.app/.netlify/functions/analyze_news`

### ✅ 測試 GitHub Actions
1. [ ] 前往 `Actions` 頁面
2. [ ] 選擇 "每日日本新聞分析" workflow
3. [ ] 點擊 "Run workflow" 手動執行
4. [ ] 檢查執行日誌是否成功
5. [ ] 確認能正常觸發 Netlify Function

## 🗄️ Supabase 設定

### ✅ 建立資料表
在 Supabase SQL Editor 中執行:
```sql
CREATE TABLE selected_news (
    id UUID PRIMARY KEY,
    date VARCHAR(8) NOT NULL,
    title TEXT NOT NULL,
    reason TEXT NOT NULL,
    writing_direction TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_selected_news_date ON selected_news(date);
CREATE INDEX idx_selected_news_created_at ON selected_news(created_at);
```

### ✅ 驗證資料表
- [ ] 資料表建立成功
- [ ] 索引建立成功
- [ ] 測試執行後能在資料表中看到資料

## 🧪 完整測試

### ✅ 端到端測試
1. [ ] GitHub Actions 自動觸發 (等待定時執行或手動觸發)
2. [ ] Netlify Function 成功執行
3. [ ] 資料成功儲存到 Supabase
4. [ ] 檢查資料內容正確

### ✅ 查詢測試資料
```sql
-- 查看最新的分析結果
SELECT date, title, reason, created_at 
FROM selected_news 
ORDER BY created_at DESC 
LIMIT 5;
```

## ⏰ 自動執行驗證

### ✅ 時間設定確認
- [ ] GitHub Actions cron: `0 18 * * *` (UTC 18:00)
- [ ] 對應日本時間: 凌晨 3:00 (JST)
- [ ] 分析目標: 前一天的新聞

### ✅ 首次自動執行
等待第一次自動執行 (或手動觸發):
- [ ] GitHub Actions 在預定時間執行
- [ ] Netlify Function 被成功觸發
- [ ] 新聞分析完成並儲存
- [ ] 無錯誤或異常狀況

## 📊 監控設定

### ✅ 日誌監控
設定以下監控點:
- [ ] Netlify Function logs
- [ ] GitHub Actions execution logs  
- [ ] Supabase database logs
- [ ] OpenAI API usage monitoring

### ✅ 通知設定 (可選)
- [ ] Slack webhook 通知
- [ ] Email 通知
- [ ] Discord 通知

## 🔧 最佳化設定

### ✅ 效能調整
- [ ] 調整分析的標題數量 (預設 50)
- [ ] 設定合適的 Function timeout
- [ ] 監控 API 使用量

### ✅ 錯誤處理
- [ ] 測試網路錯誤情況
- [ ] 測試 API 額度不足情況
- [ ] 測試新聞源無回應情況

## ✅ 完成確認

### 最終檢查
- [ ] ✅ 服務能每日自動執行
- [ ] ✅ 每次都能選出 5 則新聞
- [ ] ✅ 資料正確儲存到資料庫
- [ ] ✅ 所有日誌正常無錯誤
- [ ] ✅ 成本控制在預期範圍內

---

## 🎉 恭喜！

如果所有項目都已勾選，你的日本新聞分析服務已經成功部署並開始自動運作！

### 📞 後續維護
- 定期檢查服務運作狀況
- 監控 API 使用量和成本
- 適時更新程式邏輯和選擇標準
- 備份重要資料

### 🐛 如遇問題
1. 檢查相關日誌
2. 參考故障排除文檔
3. 查看 GitHub Issues
4. 聯繫技術支援