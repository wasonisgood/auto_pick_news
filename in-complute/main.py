import os
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()
import sys
import subprocess
import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client

# 🛠️ 自動安裝所需套件
def ensure_package(pkg):
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

for p in ['ollama', 'supabase']:
    ensure_package(p)

import ollama
from supabase import create_client

# 🧠 確保 llama4 模型存在
def ensure_llama_model():
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if "llama4:128x17b" not in result.stdout:
        print("⬇️ Pull llama4:128x17b...")
        subprocess.run(["ollama", "pull", "llama4:128x17b"], check=True)

# 🔐 Supabase 初始化
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🌐 抓取 RSS
def fetch_rss(date_str):
    url = f"https://japan-news-get.netlify.app/rss?date={date_str}"
    res = requests.get(url)
    res.raise_for_status()
    return res.text

def parse_titles(rss_xml):
    root = ET.fromstring(rss_xml)
    items = root.findall(".//item")
    titles = []
    for item in items:
        title = item.find("title").text.strip()
        if any(skip in title for skip in ["Yahoo Japan トップニュース", "地震情報"]):
            continue
        titles.append(title)
    return titles

# 🤖 呼叫 LLM
def analyze_titles(titles):
    prompt = f"""
你是一位為臺灣製作國際新聞的日本觀察站新聞編輯。請從下列日本新聞標題中選出最值得報導的5則：

標題如下：
{json.dumps(titles, ensure_ascii=False, indent=2)}

選擇標準如下：
- 增進台灣人對日本的政治、經濟、外交與文化理解
- 對於理解美中台關係有參考價值
- 在可能的台海衝突中，有助於建立對日認知與因應策略

請輸出 JSON 格式，包含：
1. 選出的5個標題
2. 為何選擇（每個簡要說明）
3. 每則建議的寫作方向與角度
"""
    res = ollama.chat(
        model="llama4:128x17b",
        messages=[{"role": "user", "content": prompt}]
    )
    return res["message"]["content"]

# 💾 寫入 Supabase
def store_to_supabase(date_str, source, result):
    supabase.table("rss_selection_log").insert({
        "date": date_str,
        "source": source,
        "result": json.loads(result),
        "fetched_at": datetime.utcnow().isoformat()
    }).execute()

# 📤 發送 Webhook
def send_webhook(result_json):
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ 未設定 WEBHOOK_URL")
        return
    try:
        requests.post(webhook_url, json=result_json)
        print("✅ Webhook 已送出")
    except Exception as e:
        print("❌ Webhook 發送錯誤：", str(e))

# 🧭 主流程
def main():
    ensure_llama_model()
    JST = timezone(timedelta(hours=9))
    today = datetime.now(JST).strftime('%Y%m%d')
    yesterday = (datetime.now(JST) - timedelta(days=1)).strftime('%Y%m%d')

    titles = []
    for d in [yesterday, today]:
        try:
            xml = fetch_rss(d)
            titles += parse_titles(xml)
        except Exception as e:
            print(f"⚠️ RSS {d} 讀取失敗：{e}")

    if not titles:
        print("❌ 沒有可用標題")
        return

    print("🤖 分析中...")
    llm_result = analyze_titles(titles)

    print("📦 儲存中...")
    store_to_supabase(today, "rss", llm_result)

    print("📡 傳送通知...")
    send_webhook({
        "date": today,
        "source": "rss",
        "llm_result": json.loads(llm_result)
    })

if __name__ == "__main__":
    main()
