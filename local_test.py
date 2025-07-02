# local_test.py
"""
本地測試腳本 - 在部署前測試 Netlify Function 功能
執行前請確保已設定環境變數或 .env 檔案
"""

import json
import os
import sys
from pathlib import Path

# 加入 netlify/functions 到路徑以便導入
sys.path.append(str(Path(__file__).parent / "netlify" / "functions"))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ 未安裝 python-dotenv，跳過 .env 檔案載入")

def check_environment():
    """檢查環境變數設定"""
    print("🔍 檢查環境變數...")
    
    required_vars = [
        "OPENAI_API_KEY",
        "SUPABASE_URL", 
        "SUPABASE_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # 隱藏敏感資訊
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"  ✅ {var}: {display_value}")
    
    if missing_vars:
        print(f"  ❌ 缺少環境變數: {', '.join(missing_vars)}")
        return False
    
    print("  ✅ 所有環境變數已設定")
    return True

def test_imports():
    """測試套件導入"""
    print("\n📦 測試套件導入...")
    
    required_packages = [
        ("openai", "OpenAI"),
        ("supabase", "create_client"), 
        ("pydantic", "BaseModel"),
        ("requests", "get")
    ]
    
    missing_packages = []
    for package, import_item in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package}")
    
    if missing_packages:
        print(f"\n請安裝缺少的套件:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def test_function_import():
    """測試 Netlify Function 導入"""
    print("\n🔧 測試 Function 導入...")
    
    try:
        from netlify.functions.analyze_news import handler
        print("  ✅ Netlify Function 導入成功")
        return handler
    except ImportError as e:
        print(f"  ❌ Function 導入失敗: {e}")
        return None

def test_function_execution(handler):
    """測試 Function 執行"""
    print("\n🚀 測試 Function 執行...")
    
    # 模擬 Netlify event 和 context
    test_event = {
        "httpMethod": "POST",
        "body": json.dumps({"test": True})
    }
    test_context = {}
    
    try:
        print("  🔄 執行 Function...")
        result = handler(test_event, test_context)
        
        print(f"  📊 HTTP 狀態碼: {result['statusCode']}")
        
        # 解析回應內容
        try:
            response_body = json.loads(result['body'])
            
            if response_body.get('success'):
                print("  ✅ Function 執行成功!")
                
                # 顯示關鍵資訊
                data = response_body.get('data', {})
                print(f"    📅 分析日期: {data.get('date', 'N/A')}")
                print(f"    📰 總標題數: {data.get('total_titles', 'N/A')}")
                print(f"    ✅ 選中新聞: {data.get('selected_count', 'N/A')}")
                print(f"    💾 儲存數量: {data.get('saved_count', 'N/A')}")
                print(f"    ⏱️ 執行時間: {data.get('execution_time_seconds', 'N/A')} 秒")
                
                # 顯示選中的新聞
                selected_news = data.get('selected_news', [])
                if selected_news:
                    print("\n  📋 選中的新聞:")
                    for i, news in enumerate(selected_news, 1):
                        title = news.get('title', 'N/A')
                        print(f"    {i}. {title[:50]}{'...' if len(title) > 50 else ''}")
                
                return True
                
            else:
                print(f"  ❌ Function 執行失敗: {response_body.get('message', '未知錯誤')}")
                
                # 顯示錯誤日誌
                logs = response_body.get('logs', [])
                if logs:
                    print("  📝 執行日誌:")
                    for log in logs:
                        print(f"    {log}")
                
                return False
                
        except json.JSONDecodeError:
            print(f"  ❌ 回應格式錯誤: {result['body'][:200]}...")
            return False
            
    except Exception as e:
        print(f"  ❌ Function 執行異常: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_deployment_info():
    """顯示部署資訊"""
    print(f"\n{'='*50}")
    print("🚀 部署前準備清單")
    print('='*50)
    print("1. ✅ 本地測試通過")
    print("2. 📁 確認檔案結構正確:")
    print("   netlify/functions/analyze_news.py")
    print("   .github/workflows/daily-news-analysis.yml") 
    print("   netlify.toml")
    print("   requirements.txt")
    print("   public/index.html")
    print()
    print("3. 🔧 部署到 Netlify:")
    print("   - 連接 GitHub 儲存庫")
    print("   - 設定環境變數")
    print("   - 部署網站")
    print()
    print("4. ⚙️ 設定 GitHub Secrets:")
    print("   - NETLIFY_FUNCTION_URL")
    print()
    print("5. 🗄️ 建立 Supabase 資料表")
    print()
    print("6. 🧪 測試部署結果")

def main():
    """主測試流程"""
    print("🧪 日本新聞分析服務 - 本地測試")
    print("="*50)
    
    # 檢查環境
    if not check_environment():
        print("\n❌ 環境變數設定不完整，請先設定 .env 檔案或環境變數")
        return False
    
    # 檢查套件
    if not test_imports():
        print("\n❌ 套件安裝不完整，請執行 pip install -r requirements.txt")
        return False
    
    # 測試 Function 導入
    handler = test_function_import()
    if not handler:
        print("\n❌ Function 導入失敗，請檢查檔案路徑")
        return False
    
    # 測試 Function 執行
    success = test_function_execution(handler)
    
    if success:
        print(f"\n{'='*50}")
        print("🎉 所有測試通過！準備部署到 Netlify")
        print('='*50)
        show_deployment_info()
    else:
        print(f"\n{'='*50}")
        print("❌ 測試失敗，請檢查錯誤訊息並修正")
        print('='*50)
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試過程發生異常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)