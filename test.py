# netlify/functions/test.py - 最小化測試函數
import json
import os
from datetime import datetime

def handler(event, context):
    """最簡單的測試函數"""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "message": "Test function is working!",
            "timestamp": datetime.now().isoformat(),
            "event_method": event.get("httpMethod", "unknown"),
            "environment_vars": {
                "openai_key_exists": bool(os.environ.get("OPENAI_API_KEY")),
                "supabase_url_exists": bool(os.environ.get("SUPABASE_URL")),
                "supabase_key_exists": bool(os.environ.get("SUPABASE_KEY"))
            }
        })
    }

# Lambda 兼容性
lambda_handler = handler

if __name__ == "__main__":
    test_event = {"httpMethod": "GET"}
    test_context = {}
    result = handler(test_event, test_context)
    print(json.dumps(json.loads(result["body"]), indent=2))