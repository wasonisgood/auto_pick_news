#!/usr/bin/env python3
"""
日本新聞自動分析服務 - 一鍵設定腳本
執行此腳本來自動設定環境和檢查配置
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_step(step, message):
    """印出安裝步驟"""
    print(f"\n{'='*50}")
    print(f"步驟 {step}: {message}")
    print('='*50)

def check_python_version():
    """檢查 Python 版本"""
    if sys.version_info < (3, 8):
        print("❌ 錯誤：需要 Python 3.8 或更高版本")
        print(f"   當前版本：{sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python 版本檢查通過：{sys.version.split()[0]}")

def install_requirements():
    """安裝必要套件"""
    requirements = [
        "openai>=1.0.0",
        "supabase>=2.0.0", 
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "requests>=2.28.0"
    ]
    
    # 建立 requirements.txt
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(requirements))
    
    print("✅ 已建立 requirements.txt")
    
    # 安裝套件
    try:
        print("🔄 安裝 Python 套件...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 套件安裝完成")
    except subprocess.CalledProcessError:
        print("❌ 套件安裝失敗，請手動執行：pip install -r requirements.txt")
        return False
    return True

def setup_env_file():
    """設定環境變數檔案"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("⚠️  .env 檔案已存在，跳過建立")
        return True
    
    if env_example.exists():
        # 複製範例檔案
        shutil.copy(env_example, env_file)
        print("✅ 已從 .env.example 建立 .env 檔案")
    else:
        # 建立基本的 .env 檔案
        env_content = """# OpenAI API 設定
# 請到 https://platform.openai.com/api-keys 取得你的 API 金鑰
OPENAI_API_KEY=sk-your-openai-api-key-here

# Supabase 設定  
# 請到你的 Supabase 專案 Settings > API 取得以下資訊
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here
"""
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        print("✅ 已建立 .env 檔案")
    
    print("\n⚠️  重要：請編輯 .env 檔案並填入你的實際 API 金鑰")
    return True

def check_env_config():
    """檢查環境變數配置"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        openai_key = os.getenv("OPENAI_API_KEY")
        supabase_url = os.getenv("SUPABASE_URL") 
        supabase_key = os.getenv("SUPABASE_KEY")
        
        issues = []
        
        if not openai_key or openai_key == "sk-your-openai-api-key-here":
            issues.append("❌ OPENAI_API_KEY 未設定或仍為預設值")
        else:
            print("✅ OPENAI_API_KEY 已設定")
            
        if not supabase_url or supabase_url == "https://your-project-id.supabase.co":
            issues.append("❌ SUPABASE_URL 未設定或仍為預設值")
        else:
            print("✅ SUPABASE_URL 已設定")
            
        if not supabase_key or supabase_key == "your-supabase-anon-key-here":
            issues.append("❌ SUPABASE_KEY 未設定或仍為預設值")
        else:
            print("✅ SUPABASE_KEY 已設定")
        
        if issues:
            print("\n⚠️  環境變數配置問題：")
            for issue in issues:
                print(f"   {issue}")
            return False
        else:
            print("✅ 所有環境變數配置正確")
            return True
            
    except ImportError:
        print("❌ 無法導入 dotenv，請確認套件安裝成功")
        return False

def test_connections():
    """測試 API 連線"""
    print("🔄 測試 API 連線...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # 測試 OpenAI
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            # 簡單的測試請求
            response = client.models.list()
            print("✅ OpenAI API 連線測試成功")
        except Exception as e:
            print(f"❌ OpenAI API 連線失敗：{e}")
            return False
        
        # 測試 Supabase
        try:
            from supabase import create_client
            supabase = create_client(
                os.getenv("SUPABASE_URL"), 
                os.getenv("SUPABASE_KEY")
            )
            # 簡單的測試查詢
            response = supabase.table("selected_news").select("*").limit(1).execute()
            print("✅ Supabase 連線測試成功")
        except Exception as e:
            print(f"❌ Supabase 連線失敗：{e}")
            print("   請確認資料表 'selected_news' 已建立")
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ 導入套件失敗：{e}")
        return False

def show_next_steps():
    """顯示後續步驟"""
    print(f"\n{'='*50}")
    print("🎉 設定完成！")
    print('='*50)
    print("\n📋 後續步驟：")
    print("1. 確認 Supabase 中已建立 'selected_news' 資料表")
    print("2. 執行主程式：python gpt.py")
    print("3. 查看執行日誌確認運作正常")
    print("\n📚 更多資訊請參考 README.md")
    
    print("\n🗃️  建立 Supabase 資料表的 SQL：")
    print("""
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
""")

def main():
    """主要安裝流程"""
    print("🚀 日本新聞自動分析服務 - 一鍵設定")
    
    print_step(1, "檢查 Python 版本")
    check_python_version()
    
    print_step(2, "安裝必要套件")
    if not install_requirements():
        return
    
    print_step(3, "設定環境變數檔案")
    setup_env_file()
    
    print_step(4, "檢查環境變數配置")
    env_ok = check_env_config()
    
    if env_ok:
        print_step(5, "測試 API 連線")
        test_connections()
    
    show_next_steps()

if __name__ == "__main__":
    main()