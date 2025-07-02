# 日本新聞分析服務 - Netlify + GitHub Actions 部署指南 🚀

> 使用 Netlify Functions 和 GitHub Actions 建立自動化的日本新聞分析服務，每天日本時間凌晨 3:00 自動執行。

## 📁 專案結構

```
your-repo/
├── .github/
│   └── workflows/
│       └── daily-news-analysis.yml    # GitHub Actions 工作流程
├── netlify/
│   └── functions/
│       └── analyze_news.py            # Netlify Function 主程式
├── public/
│   └── index.html                     # 測試頁面
├── netlify.toml                       # Netlify 配置
├── requirements.txt                   # Python 依賴套件
└── README.md                          # 本文檔
```

## 🚀 快速部署

### 步驟 1: 準備 GitHub 儲存庫

1. **建立新的 GitHub 儲存庫**
2. **上傳所有檔案** 到儲存庫根目錄
3. **確認檔案結構** 符合上述專案結構

### 步驟 2: 部署到 Netlify

1. **登入 Netlify**
   - 前往 [netlify.com](https://netlify.com)
   - 使用 GitHub 帳戶登入

2. **連接 GitHub 儲存庫**
   ```
   New site from Git → GitHub → 選擇你的儲存庫
   ```

3. **配置構建設定**
   ```
   Build command: (留空)
   Publish directory: public
   Functions directory: netlify/functions
   ```

4. **部署網站**
   - 點擊 "Deploy site"
   - 等待部署完成

### 步驟 3: 設定環境變數

在 Netlify 控制台中設定以下環境變數：

1. **前往 Site settings → Environment variables**

2. **加入必要的環境變數：**
   ```
   OPENAI_API_KEY = sk-your-openai-api-key
   SUPABASE_URL = https://your-project.supabase.co  
   SUPABASE_KEY = your-supabase-anon-key
   ```

### 步驟 4: 設定 GitHub Secrets

為了讓 GitHub Actions 能觸發 Netlify Function：

1. **取得 Netlify Function URL**
   ```
   格式: https://your-site-name.netlify.app/.netlify/functions/analyze_news
   ```

2. **在 GitHub 儲存庫設定 Secrets**
   ```
   Settings → Secrets and variables → Actions → New repository secret
   
   名稱: NETLIFY_FUNCTION_URL
   值: https://your-site-name.netlify.app/.netlify/functions/analyze_news
   ```

### 步驟 5: 設定 Supabase 資料表

在 Supabase SQL Editor 中執行：

```sql
CREATE TABLE selected_news (
    id UUID PRIMARY KEY,
    date VARCHAR(8) NOT NULL,
    title TEXT NOT NULL,
    reason TEXT NOT NULL,
    writing_direction TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 建立索引
CREATE INDEX idx_selected_news_date ON selected_news(date);
CREATE INDEX idx_selected_news_created_at ON selected_news(created_at);
```

## ⏰ 自動執行時程

- **執行時間**: 每天 UTC 18:00 (日本時間凌晨 3:00)
- **分析目標**: 前一天的日本新聞
- **自動觸發**: GitHub Actions Cron Job

## 🧪 測試部署

### 1. 測試 Netlify Function

訪問你的網站測試頁面：
```
https://your-site-name.netlify.app
```

點擊 "手動觸發分析" 按鈕測試功能。

### 2. 測試 GitHub Actions

**手動觸發 GitHub Actions：**
1. 前往 GitHub 儲存庫
2. Actions → 選擇 "每日日本新聞分析"
3. Run workflow → Run workflow

### 3. 直接 API 測試

```bash
# 使用 curl 測試
curl -X POST https://your-site-name.netlify.app/.netlify/functions/analyze_news \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 📊 監控和日誌

### Netlify Function 日誌
```
Netlify Dashboard → Functions → analyze_news → Function log
```

### GitHub Actions 日誌
```
GitHub → Actions → 選擇執行記錄 → 查看詳細日誌
```

### Supabase 資料查詢
```sql
-- 查看最近的分析結果
SELECT date, title, created_at 
FROM selected_news 
ORDER BY created_at DESC 
LIMIT 10;

-- 統計每日分析數量
SELECT date, COUNT(*) as count 
FROM selected_news 
GROUP BY date 
ORDER BY date DESC;
```

## 🔧 自訂配置

### 修改執行時間

編輯 `.github/workflows/daily-news-analysis.yml`:
```yaml
schedule:
  # 修改 cron 表達式
  - cron: '0 18 * * *'  # UTC 18:00 = JST 03:00
```

### 修改選擇標準

編輯 `netlify/functions/analyze_news.py` 中的 prompt。

### 加入通知功能

在 GitHub Actions 中加入 Slack/Discord/Email 通知：

```yaml
- name: 發送成功通知
  if: success()
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK_URL }} \
      -H "Content-Type: application/json" \
      -d '{"text": "✅ 日本新聞分析完成"}'
```

## 🛠 故障排除

### 常見問題

**❌ Function 執行逾時**
```
解決方案: 
1. 減少分析的標題數量 (limited_titles[:30])
2. 檢查 API 回應時間
3. 調整 netlify.toml 中的 timeout 設定
```

**❌ GitHub Actions 無法觸發 Function**
```
檢查項目:
1. NETLIFY_FUNCTION_URL secret 是否正確
2. Netlify Function 是否正常部署
3. 網路連線是否正常
```

**❌ 環境變數未設定**
```
確認步驟:
1. Netlify 環境變數是否正確設定
2. 重新部署 Netlify 站點
3. 檢查變數名稱拼寫
```

**❌ GPT API 額度不足**
```
解決方案:
1. 檢查 OpenAI 帳戶餘額
2. 設定用量限制
3. 考慮使用更便宜的模型
```

### 偵錯模式

**啟用詳細日誌：**
1. 在 Netlify Function 中加入更多 log_messages
2. 在 GitHub Actions 中加入 debug 輸出
3. 檢查 Supabase 日誌

## 💰 成本估算

### Netlify
- **免費方案**: 125,000 Function 呼叫/月
- **每日執行一次**: 約 30 次/月 (遠低於限制)

### OpenAI API
- **每次執行**: 約 1,000-3,000 tokens
- **每月成本**: 約 $1-3 USD

### Supabase
- **免費方案**: 500MB 資料庫，50,000 行
- **每日 5 則新聞**: 約 150 行/月 (遠低於限制)

### GitHub Actions
- **免費方案**: 2,000 分鐘/月
- **每日執行**: 約 5 分鐘/月 (遠低於限制)

**總計**: 幾乎免費使用 🎉

## 📈 擴展功能

### 1. 多語言支援
- 加入其他國家的新聞源
- 支援多種語言分析

### 2. 智能通知
- 重要新聞即時推送
- 自訂關鍵字提醒

### 3. 資料視覺化
- 新聞趨勢圖表
- 主題分類統計

### 4. API 介面
- 提供 REST API
- 支援第三方整合

## 🤝 維護指南

### 定期檢查項目
- [ ] API 金鑰是否過期
- [ ] 資料庫容量是否足夠
- [ ] 新聞源是否正常
- [ ] 執行結果是否符合預期

### 更新頻率
- **程式碼**: 依需求更新
- **依賴套件**: 每月檢查更新
- **API 版本**: 關注官方公告

## 📞 支援

如有問題請檢查：
1. GitHub Issues
2. Netlify 文檔
3. OpenAI API 文檔
4. Supabase 文檔

---

**🎉 恭喜！** 你已經成功建立了一個全自動的日本新聞分析服務！