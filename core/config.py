# core/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# 1. 自動搵出根目錄嘅 .env 絕對路徑
# __file__ 係 config.py -> parent 係 core/ -> parent 係根目錄
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# 2. 喺定義 Class 之前就載入變數
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
    print(f"✅ [Config] 成功載入環境變數: {ENV_PATH}")
else:
    print(f"⚠️ [Config] 搵唔到 .env 檔案: {ENV_PATH}")

class Settings:
    # 使用 os.getenv 並提供預設值，防止 NoneType 報錯
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Local News System")  
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD") 
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

    def validate(self):
        """[Observability] 啟動時檢查關鍵變數"""
        if not self.ADMIN_PASSWORD:
            raise ValueError("❌ ADMIN_PASSWORD 係空的！請檢查 .env 內容。")
        if not self.SECRET_KEY:
            raise ValueError("❌ JWT_SECRET_KEY 係空的！請檢查 .env 內容。")

settings = Settings()
# 啟動時即刻驗證
try:
    settings.validate()
except Exception as e:
    print(str(e))