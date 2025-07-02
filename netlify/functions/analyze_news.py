# netlify/functions/analyze_news.py
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import List, Any
from uuid import uuid4

import requests
from pydantic import BaseModel, model_validator
from openai import OpenAI
from supabase import create_client, Client

# 初始化客戶端
def get_clients():
    """初始化 OpenAI 和 Supabase 客戶端"""
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    supabase_client = create_client(
        os.environ["SUPABASE_URL"], 
        os.environ["SUPABASE_KEY"]
    )
    return openai_client, supabase_client

# Pydantic 模型
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
            possible_keys = [
                'selections', 'selected_articles', 'articles',
                'news', 'selected_news', 'items', 'results'
            ]
            
            for key in possible_keys:
                if key in data and isinstance(data[key], list):
                    selections_data = data[key]
                    
                    if len(selections_data) == 0:
                        raise ValueError('選項陣列不能為空')
                    
                    cleaned_selections = []
                    for i, item in enumerate(selections_data):
                        if isinstance(item, dict):
                            cleaned_item = {
                                'title': item.get('title', f'新聞 {i+1}'),
                                'reason': item.get('reason', '未提供理由'),
                                'writing_direction': item.get('writing_direction', '未提供建議')
                            }
                            cleaned_selections.append(cleaned_item)
                    
                    return {'selections': cleaned_selections}
        
        return data

def fetch_rss(date_str):
    """抓取 RSS XML"""
    url = f"https://japan-news-get.netlify.app/rss?date={date_str}"
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        raise Exception(f"RSS 錯誤：{response.status_code}")
    return response.text

def parse_rss_titles(rss_xml):
    """解析 XML 標題"""
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

def analyze_with_gpt(titles: List[str], openai_client) -> HeadlineSelection:
    """使用 GPT 分析新聞"""
    prompt = """
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

請嚴格按照以下格式回傳，務必包含 5 則新聞：
{
  "selections": [
    {
      "title": "新聞標題",
      "reason": "選擇理由", 
      "writing_direction": "建議撰寫角度"
    }
  ]
}

**強制要求：陣列中必須有正好 5 個新聞物件，絕對不可以是空陣列或少於 5 個項目。**
"""
    
    # 限制標題數量避免 token 過多
    limited_titles = titles[:50]
    
    messages = [
        {
            "role": "system", 
            "content": "你是專業的新聞編輯。最重要的規則：無論如何都必須選出正好5則新聞。請嚴格按照JSON格式回傳結果。"
        },
        {
            "role": "user", 
            "content": prompt + "\n\n新聞標題：\n" + "\n".join([f"- {title}" for title in limited_titles])
        }
    ]
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3
    )
    
    parsed = HeadlineSelection.model_validate_json(response.choices[0].message.content)
    return parsed

def save_to_database(date_str: str, selection: HeadlineSelection, supabase_client):
    """儲存到 Supabase 資料庫"""
    success_count = 0
    errors = []
    
    for item in selection.selections:
        try:
            data = {
                "id": str(uuid4()),
                "date": date_str,
                "title": item.title,
                "reason": item.reason,
                "writing_direction": item.writing_direction,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            res = supabase_client.table("selected_news").insert(data).execute()
            
            if hasattr(res, 'data') and res.data:
                success_count += 1
            else:
                errors.append(f"儲存失敗：{item.title[:30]}...")
                
        except Exception as e:
            errors.append(f"錯誤：{str(e)}")
    
    return success_count, errors

def handler(event, context):
    """Netlify Function 主處理函數"""
    
    # 記錄執行開始
    start_time = datetime.now(timezone.utc)
    log_messages = []
    
    try:
        # 初始化客戶端
        openai_client, supabase_client = get_clients()
        log_messages.append("✅ 客戶端初始化成功")
        
        # 計算目標日期（日本時間）
        JST = timezone(timedelta(hours=9))
        now_jst = datetime.now(JST)
        
        # 總是分析前一天的新聞（因為凌晨3點執行）
        target_date = (now_jst - timedelta(days=1)).strftime('%Y%m%d')
        log_messages.append(f"📅 目標分析日期：{target_date}")
        
        # 抓取新聞
        log_messages.append(f"📡 開始抓取 {target_date} 的新聞...")
        rss_xml = fetch_rss(target_date)
        titles = parse_rss_titles(rss_xml)
        
        if not titles:
            raise Exception("未取得任何新聞標題")
        
        # 去重複
        unique_titles = list(dict.fromkeys(titles))
        log_messages.append(f"📰 取得 {len(titles)} 則標題，去重後 {len(unique_titles)} 則")
        
        # GPT 分析
        log_messages.append("🧠 開始 GPT 分析...")
        selection = analyze_with_gpt(unique_titles, openai_client)
        log_messages.append(f"✅ GPT 分析完成，選出 {len(selection.selections)} 則新聞")
        
        # 儲存到資料庫
        log_messages.append("💾 開始儲存到資料庫...")
        success_count, errors = save_to_database(target_date, selection, supabase_client)
        
        # 準備回應
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        result = {
            "success": True,
            "message": f"成功分析並儲存 {success_count} 則新聞",
            "data": {
                "date": target_date,
                "total_titles": len(titles),
                "unique_titles": len(unique_titles),
                "selected_count": len(selection.selections),
                "saved_count": success_count,
                "selected_news": [
                    {
                        "title": item.title,
                        "reason": item.reason[:100] + "..." if len(item.reason) > 100 else item.reason,
                        "writing_direction": item.writing_direction[:100] + "..." if len(item.writing_direction) > 100 else item.writing_direction
                    }
                    for item in selection.selections
                ],
                "execution_time_seconds": round(execution_time, 2)
            },
            "logs": log_messages,
            "errors": errors if errors else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(result, ensure_ascii=False, indent=2)
        }
        
    except Exception as e:
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        error_result = {
            "success": False,
            "message": f"執行失敗：{str(e)}",
            "logs": log_messages,
            "execution_time_seconds": round(execution_time, 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(error_result, ensure_ascii=False, indent=2)
        }

# 為了本地測試
if __name__ == "__main__":
    # 模擬 Netlify event 和 context
    test_event = {}
    test_context = {}
    
    result = handler(test_event, test_context)
    print(json.dumps(json.loads(result["body"]), ensure_ascii=False, indent=2))