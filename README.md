# 日本新聞自動分析服務 📰🤖

> 自動抓取日本新聞標題，使用 GPT 智能分析並選出對台灣具有參考價值的重要新聞，儲存至資料庫供後續使用。

## 🌟 功能特色

- 🔄 **自動新聞抓取**：每日自動從日本新聞 RSS 源抓取最新標題
- 🧠 **AI 智能分析**：使用 GPT-4o-mini 分析新聞重要性和相關性
- 🎯 **台灣視角篩選**：專注選出對台灣政治、經濟、外交具參考價值的新聞
- 💾 **雲端資料庫**：自動儲存分析結果至 Supabase 資料庫
- 📊 **詳細日誌**：提供完整的處理過程記錄和錯誤追蹤
- ⏰ **時間彈性**：根據當前時間智能選擇分析日期範圍

## 📋 系統需求

- Python 3.8+
- OpenAI API 金鑰
- Supabase 帳戶和 API 金鑰
- 網路連線

## 🚀 快速開始

### 1. 環境設定

```bash
# 複製專案
git clone <repository-url>
cd auto_pick_news

# 安裝依賴套件
pip install -r requirements.txt
```

### 2. 建立依賴套件清單

創建 `requirements.txt` 檔案：

```txt
openai>=1.0.0
supabase>=2.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
requests>=2.28.0
```

### 3. 環境變數設定

創建 `.env` 檔案並填入以下資訊：

```env
# OpenAI API 設定
OPENAI_API_KEY=sk-your-openai-api-key-here

# Supabase 設定
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here
```

### 4. Supabase 資料表設定

在你的 Supabase 專案中建立 `selected_news` 資料表：

```sql
CREATE TABLE selected_news (
    id UUID PRIMARY KEY,
    date VARCHAR(8) NOT NULL,
    title TEXT NOT NULL,
    reason TEXT NOT NULL,
    writing_direction TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 建立索引以提升查詢效能
CREATE INDEX idx_selected_news_date ON selected_news(date);
CREATE INDEX idx_selected_news_created_at ON selected_news(created_at);
```

## 🏃‍♂️ 執行服務

```bash
python gpt.py
```

## 📊 執行邏輯

### 時間策略
- **早於下午 3 點**：分析前兩天的新聞
- **下午 3 點後**：分析昨天和今天的新聞

### 分析流程
1. **RSS 抓取**：從 `https://japan-news-get.netlify.app/rss` 抓取指定日期的新聞
2. **標題過濾**：自動過濾掉 "Yahoo Japan"、"地震情報" 等無關標題
3. **GPT 分析**：將標題送給 GPT 進行智能分析和篩選
4. **結果儲存**：將選中的 5 則新聞儲存到 Supabase 資料庫
5. **結果確認**：自動查詢資料庫確認儲存成功

## 📁 專案結構

```
auto_pick_news/
├── gpt.py              # 主程式檔案
├── requirements.txt    # Python 依賴套件
├── .env               # 環境變數 (需自行建立)
├── .env.example       # 環境變數範例
└── README.md          # 說明文件
```

## 🔧 設定說明

### OpenAI API 設定
1. 前往 [OpenAI Platform](https://platform.openai.com/api-keys)
2. 建立新的 API 金鑰
3. 將金鑰加入 `.env` 檔案

### Supabase 設定
1. 前往 [Supabase](https://supabase.com) 建立專案
2. 在 Project Settings > API 找到你的 URL 和 anon key
3. 在 SQL Editor 中執行上述建表語句
4. 將設定加入 `.env` 檔案

## 📈 輸出範例

```
🕐 當前時間：2025-07-02 14:30:00 JST
🌅 早於下午3點，分析前兩天的新聞
📋 目標日期：['20250630', '20250701']

📡 抓取 RSS：20250630
   ✅ 取得 78 則標題
📡 抓取 RSS：20250701
   ✅ 取得 83 則標題

🧠 開始分析，去重後共 145 則
📊 將選出 5 則重要新聞
📝 發送給 GPT 的標題數量：50
🔧 使用鍵名：selections
✅ 成功處理 5 則新聞
✅ GPT 分析成功，選出 5 則新聞

📋 選中的新聞：
1. 日本央行維持超低利率政策不變
2. 日中關係因釣魚台問題再度緊張
3. 日本防衛費預算創歷史新高
4. 日本與東南亞加強經濟合作
5. 日本半導體産業復興計劃啟動

📊 準備儲存 5 則選中的新聞到 Supabase
✅ 已儲存：日本央行維持超低利率政策不變
✅ 已儲存：日中關係因釣魚台問題再度緊張
✅ 已儲存：日本防衛費預算創歷史新高
✅ 已儲存：日本與東南亞加強經濟合作
✅ 已儲存：日本半導體産業復興計劃啟動

📈 儲存結果：成功 5 則，失敗 0 則
🎉 資料已儲存到 Supabase 表格 'selected_news'
```

## 🔍 資料庫查詢

### 查詢特定日期的新聞
```sql
SELECT * FROM selected_news 
WHERE date = '20250701' 
ORDER BY created_at DESC;
```

### 查詢最近的新聞分析
```sql
SELECT date, title, reason, writing_direction, created_at 
FROM selected_news 
ORDER BY created_at DESC 
LIMIT 10;
```

### 統計每日分析數量
```sql
SELECT date, COUNT(*) as news_count 
FROM selected_news 
GROUP BY date 
ORDER BY date DESC;
```

## 🛠 故障排除

### 常見問題

**❌ OpenAI API 錯誤**
```
檢查 API 金鑰是否正確
確認帳戶有足夠的 credits
檢查網路連線
```

**❌ Supabase 連線失敗**
```
檢查 URL 和 API 金鑰是否正確
確認資料表已正確建立
檢查防火牆設定
```

**❌ RSS 抓取失敗**
```
檢查網路連線
確認目標日期格式正確 (YYYYMMDD)
RSS 源可能暫時無法存取
```

**❌ GPT 選出 0 則新聞**
```
檢查 prompt 是否正確
確認標題數量足夠
降低篩選標準
```

### 偵錯模式

如需詳細的偵錯資訊，可以修改程式碼中的日誌等級或加入除錯輸出。

## 🔄 自動化執行

### 使用 Cron (Linux/Mac)
```bash
# 每天下午 3 點執行
0 15 * * * cd /path/to/auto_pick_news && python gpt.py
```

### 使用 Task Scheduler (Windows)
1. 開啟工作排程器
2. 建立基本工作
3. 設定觸發程序為每日下午 3 點
4. 動作選擇執行程式：`python.exe`
5. 引數填入：完整路徑到 `gpt.py`

## 📊 API 用量預估

- **每次執行**：約使用 1,000-3,000 tokens
- **每月成本**：約 $1-5 USD（依執行頻率而定）
- **建議設定**：每日執行一次

## 🤝 貢獻指南

1. Fork 本專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📝 授權

本專案採用 MIT 授權條款。

## 📞 聯絡資訊

如有問題或建議，請開啟 GitHub Issue 或聯繫專案維護者。

---

**⚠️ 注意事項**
- 請確保遵守 OpenAI 使用條款
- 請勿將 API 金鑰上傳到公開儲存庫
- 建議設定適當的錯誤處理和重試機制
- 定期備份 Supabase 資料庫

**📈 版本歷史**
- v1.0.0 - 初始版本，基本新聞分析功能
- v1.1.0 - 加入彈性的 GPT 回應格式處理
- v1.2.0 - 改進錯誤處理和日誌系統