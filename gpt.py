import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import List, Any
from uuid import uuid4

import requests
from pydantic import BaseModel, field_validator, model_validator
from openai import OpenAI
from dotenv import load_dotenv
from supabase import create_client, Client

# 載入環境變數
load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

# Pydantic Schema - 彈性版本
class SelectedHeadline(BaseModel):
    title: str
    reason: str
    writing_direction: str

class HeadlineSelection(BaseModel):
    selections: List[SelectedHeadline]
    
    @model_validator(mode='before')
    @classmethod
    def extract_selections(cls, data: Any) -> Any:
        """自動從不同的鍵名中提取選項陣列"""
        if isinstance(data, dict):
            # 按優先順序檢查可能的鍵名
            possible_keys = [
                'selections',
                'selected_articles', 
                'articles',
                'news',
                'selected_news',
                'items',
                'results'
            ]
            
            for key in possible_keys:
                if key in data and isinstance(data[key], list):
                    print(f"🔧 使用鍵名：{key}")
                    selections_data = data[key]
                    
                    # 驗證陣列不為空
                    if len(selections_data) == 0:
                        raise ValueError('選項陣列不能為空')
                    
                    # 簡單清理資料，確保每個項目都有必要的欄位
                    cleaned_selections = []
                    for i, item in enumerate(selections_data):
                        if isinstance(item, dict):
                            cleaned_item = {
                                'title': item.get('title', f'新聞 {i+1}'),
                                'reason': item.get('reason', '未提供理由'),
                                'writing_direction': item.get('writing_direction', '未提供建議')
                            }
                            cleaned_selections.append(cleaned_item)
                    
                    print(f"✅ 成功處理 {len(cleaned_selections)} 則新聞")
                    return {'selections': cleaned_selections}
            
            # 如果找不到預期的鍵，嘗試找任何陣列
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    # 檢查陣列第一個元素是否看起來像新聞項目
                    first_item = value[0]
                    if isinstance(first_item, dict) and any(k in first_item for k in ['title', 'reason']):
                        print(f"🔧 自動檢測到陣列：{key}")
                        return {'selections': value}
        
        return data

# 抓取 RSS XML
def fetch_rss(date_str):
    url = f"https://japan-news-get.netlify.app/rss?date={date_str}"
    res = requests.get(url)
    if res.status_code != 200:
        raise Exception(f"RSS 錯誤：{res.status_code}")
    return res.text

# 解析 XML 標題
def parse_rss_titles(rss_xml):
    root = ET.fromstring(rss_xml)
    items = root.findall(".//item")
    titles = []
    for item in items:
        title_element = item.find("title")
        if title_element is not None and title_element.text:
            title = title_element.text.strip()
            if any(skip in title for skip in ["Yahoo Japan", "地震情報"]):
                continue
            titles.append(title)
    return titles

# 呼叫 GPT 並解析 - 簡化版
def call_gpt_format_selection(titles: List[str]) -> HeadlineSelection:
    prompt = f"""
你是台灣的國際新聞編輯，以下是日本新聞標題，請從中選出 5 則新聞，並說明選擇理由與建議撰寫角度。

**重要指示：無論如何都必須選出正好 5 則新聞，即使標題看起來不夠有趣或不完全符合條件，也要從現有標題中選出最相關的 5 則。**

優先條件（盡量符合，但不是必須）：
1. 有助台灣理解日本政治、外交、經濟、文化
2. 能作為對中政策或區域安全參考

如果符合上述條件的新聞不足 5 則，請按以下優先順序補足：
1. 日本政治、經濟、社會重要事件
2. 日本國際關係或外交動態
3. 日本科技、產業發展
4. 任何具有新聞價值的日本相關新聞

**強制要求：**
- 必須選出正好 5 則新聞，不可以選少於 5 則
- 即使標題質量不理想，也要從給定的標題中選出最好的 5 則
- 不可以回傳空陣列或少於 5 個項目的陣列

請嚴格按照以下格式回傳，務必包含 5 則新聞：
{{
  "selections": [
    {{
      "title": "新聞標題",
      "reason": "選擇理由", 
      "writing_direction": "建議撰寫角度"
    }},
    {{
      "title": "新聞標題2",
      "reason": "選擇理由2", 
      "writing_direction": "建議撰寫角度2"
    }},
    {{
      "title": "新聞標題3",
      "reason": "選擇理由3", 
      "writing_direction": "建議撰寫角度3"
    }},
    {{
      "title": "新聞標題4",
      "reason": "選擇理由4", 
      "writing_direction": "建議撰寫角度4"
    }},
    {{
      "title": "新聞標題5",
      "reason": "選擇理由5", 
      "writing_direction": "建議撰寫角度5"
    }}
  ]
}}

**再次強調：陣列中必須有正好 5 個新聞物件，絕對不可以是空陣列或少於 5 個項目。**
"""
    
    # 限制標題數量避免 token 過多
    limited_titles = titles[:100]
    
    print(f"📝 發送給 GPT 的標題數量：{len(limited_titles)}")
    
    messages = [
        {"role": "system", "content": "你是專業的新聞編輯。**最重要的規則：無論如何都必須選出正好5則新聞，即使標題質量不理想也要選出最好的5則。絕對不可以回傳少於5個項目的陣列。** 請嚴格按照指定的JSON格式回傳結果。"},
        {"role": "user", "content": prompt + "\n\n新聞標題：\n" + "\n".join([f"- {title}" for title in limited_titles])}
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        # 直接使用 model_validate_json，讓 Pydantic 處理格式轉換
        parsed = HeadlineSelection.model_validate_json(response.choices[0].message.content)
        print(f"✅ GPT 分析成功，選出 {len(parsed.selections)} 則新聞")
        
        return parsed
        
    except Exception as e:
        print(f"❌ GPT 分析失敗：{e}")
        import traceback
        traceback.print_exc()
        raise

# 改進的儲存函數
def save_to_supabase(date_str: str, selection: HeadlineSelection):
    print(f"\n📊 準備儲存 {len(selection.selections)} 則選中的新聞到 Supabase")
    print(f"📅 日期：{date_str}")
    print(f"🗄️ 表格：selected_news")
    print("-" * 50)
    
    success_count = 0
    error_count = 0
    
    for i, item in enumerate(selection.selections, 1):
        try:
            data = {
                "id": str(uuid4()),
                "date": date_str,
                "title": item.title,
                "reason": item.reason,
                "writing_direction": item.writing_direction,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            print(f"\n📝 第 {i} 則新聞：")
            print(f"   標題：{item.title[:60]}{'...' if len(item.title) > 60 else ''}")
            print(f"   理由：{item.reason[:60]}{'...' if len(item.reason) > 60 else ''}")
            print(f"   方向：{item.writing_direction[:60]}{'...' if len(item.writing_direction) > 60 else ''}")
            
            # 執行插入
            res = supabase.table("selected_news").insert(data).execute()
            
            # Supabase 成功插入時檢查 data 是否存在
            if hasattr(res, 'data') and res.data:
                print(f"   ✅ 儲存成功！ID: {data['id'][:8]}...")
                success_count += 1
            else:
                print(f"   ⚠️ 儲存可能失敗，回應：{res}")
                error_count += 1
                
        except Exception as e:
            print(f"   ❌ 儲存失敗：{e}")
            error_count += 1
    
    print("-" * 50)
    print(f"📈 儲存結果：成功 {success_count} 則，失敗 {error_count} 則")
    
    if success_count > 0:
        print(f"🎉 資料已儲存到 Supabase 表格 'selected_news'")
        print(f"📅 可以在資料庫中查詢日期 '{date_str}' 的記錄")

# 查詢資料庫函數
def check_database(date_str=None):
    """檢查資料庫中儲存的資料"""
    print("\n🔍 檢查資料庫中的資料...")
    
    try:
        if date_str:
            # 查詢特定日期
            res = supabase.table("selected_news").select("*").eq("date", date_str).execute()
            print(f"📅 查詢日期：{date_str}")
        else:
            # 查詢最近的資料
            res = supabase.table("selected_news").select("*").order("created_at", desc=True).limit(10).execute()
            print("📅 查詢最近 10 筆資料")
        
        if res.data:
            print(f"✅ 找到 {len(res.data)} 筆記錄：")
            for i, record in enumerate(res.data, 1):
                print(f"\n{i}. ID: {record.get('id', 'N/A')[:8]}...")
                print(f"   日期: {record.get('date', 'N/A')}")
                print(f"   標題: {record.get('title', 'N/A')[:50]}...")
                print(f"   理由: {record.get('reason', 'N/A')[:50]}...")
                print(f"   建立時間: {record.get('created_at', 'N/A')}")
        else:
            print("❌ 資料庫中沒有找到資料")
            
    except Exception as e:
        print(f"❌ 查詢資料庫失敗：{e}")

# 主流程
def main():
    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST)
    hour_now = now.hour

    print(f"🕐 當前時間：{now.strftime('%Y-%m-%d %H:%M:%S')} JST")
    
    if hour_now < 15:
        target_dates = [
            (now - timedelta(days=2)).strftime('%Y%m%d'),
            (now - timedelta(days=1)).strftime('%Y%m%d')
        ]
        print("🌅 早於下午3點，分析前兩天的新聞")
    else:
        target_dates = [
            (now - timedelta(days=1)).strftime('%Y%m%d'),
            now.strftime('%Y%m%d')
        ]
        print("🌆 下午3點後，分析昨天和今天的新聞")
    
    print(f"📋 目標日期：{target_dates}")

    all_titles = []
    latest_date = target_dates[-1]

    for date_str in target_dates:
        try:
            print(f"\n📡 抓取 RSS：{date_str}")
            rss_xml = fetch_rss(date_str)
            titles = parse_rss_titles(rss_xml)
            all_titles.extend(titles)
            print(f"   ✅ 取得 {len(titles)} 則標題")
        except Exception as e:
            print(f"   ⚠️ RSS {date_str} 抓取失敗：{e}")

    if not all_titles:
        print("❌ 無新聞標題可分析")
        return

    # 去重複
    unique_titles = list(dict.fromkeys(all_titles))
    print(f"\n🧠 開始分析，去重後共 {len(unique_titles)} 則")
    print(f"📊 將選出 5 則重要新聞")
    
    try:
        result = call_gpt_format_selection(unique_titles)
        print(f"\n✅ GPT 分析完成！選出 {len(result.selections)} 則新聞")
        
        # 顯示選中的新聞列表
        print("\n📋 選中的新聞：")
        for i, item in enumerate(result.selections, 1):
            print(f"{i}. {item.title}")
        
        # 儲存到資料庫
        save_to_supabase(latest_date, result)
        
        # 執行完畢後檢查資料庫
        print("\n" + "="*60)
        check_database(latest_date)
        
    except Exception as e:
        print(f"❌ GPT 或儲存階段錯誤：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()