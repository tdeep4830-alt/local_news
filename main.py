import sys, os
print("🚀 [1/9] Python 啟動，開始 import...", flush=True)

print("🔄 [2/9] 正在 import 爬蟲模組...", flush=True)
from script.parser import pipeline
print("✅ [2/9] 爬蟲模組 import 成功", flush=True)

import time
import asyncio
import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from dotenv import load_dotenv
print("✅ [3/9] 標準庫 import 成功", flush=True)

from script.news_db import init_db
print("✅ [4/9] news_db import 成功", flush=True)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from script.append_to_google_doc import create_news_doc
import script.news_db as db
print("✅ [5/9] Google Doc / DB import 成功", flush=True)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.concurrency import run_in_threadpool
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print("✅ [6/9] FastAPI 相關 import 成功", flush=True)
from script.post_to_socialMedia import post_to_facebook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_pipelines():
    print("✅ 後台爬蟲任務已啟動...")
    RSS_URLS = [
        {"RSS": "https://www.manchestereveningnews.co.uk/news/?service=rss", "AREA": "Manchester", "SOURCE": "Manchester Evening News", "CLASS_NAME": "Paragraph_paragraph-text__PVKlh "},
        {"RSS": "https://www.liverpoolecho.co.uk/?service=rss", "AREA": "Liverpool", "SOURCE": "Liverpool Echo", "CLASS_NAME": "Paragraph_paragraph-text__PVKlh"},
        {"RSS": "https://www.wirralglobe.co.uk/?service=rss", "AREA": "Wirral", "SOURCE": "Wirral Globe", "CLASS_NAME": "article-content"}
    ]
    while True:
        try:
            print(f"[{datetime.now()}] 正在執行爬蟲程式...")
            # 這裡建議將同步的 pipeline 改為 non-blocking 或在 thread 中執行
            # 如果 pipeline 很吃資源，這是觀察 CPU 監控點
            for rss in RSS_URLS:
    # 注意：pipeline 後面「沒有」括號
                await run_in_threadpool(
                    pipeline,           # 1. 函數名
                    rss["RSS"],         # 2. 第一個參數
                    rss["AREA"],        # 3. 第二個參數
                    rss["SOURCE"],      # 4. 第三個參數
                    rss["CLASS_NAME"]   # 5. 第四個參數
                )
            print(f"[{datetime.now()}] 爬蟲完成，等待 300 秒...")
        except Exception as e:
            print(f"❌ 爬蟲出錯 (Observability Log): {e}")
        
        await asyncio.sleep(300) # 使用 asyncio.sleep 而非 time.sleep

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        print("🔧 正在初始化資料庫...")
        init_db()
        print("✅ 資料庫初始化完成")
    except Exception as e:
        print(f"❌ 資料庫初始化失敗: {e}")
    # 啟動時執行
    task = asyncio.create_task(run_pipelines())
    yield
    # 關閉時執行
    task.cancel()

app = FastAPI(lifespan=lifespan)
 

print("🔄 [7/9] 正在載入環境變數...", flush=True)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, "api", ".env"))
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM      = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
print(f"✅ [7/9] 環境變數載入完成 — ADMIN_USERNAME={'已設定' if ADMIN_USERNAME else '❌ 未設定'}, ADMIN_PASSWORD={'已設定' if ADMIN_PASSWORD else '❌ 未設定'}, JWT_SECRET_KEY={'已設定' if SECRET_KEY else '❌ 未設定'}", flush=True)

oauth2_scheme   = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

if not ADMIN_PASSWORD or not SECRET_KEY:
    raise RuntimeError("❌ 缺少必要環境變數：ADMIN_PASSWORD 或 JWT_SECRET_KEY 未設定。請在 Render 的 Environment 頁面新增。")

print("🔄 [8/9] 正在生成 bcrypt hash...", flush=True)
HASHED_PASSWORD = bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt())
print("✅ [8/9] bcrypt hash 生成成功", flush=True)

download_path = os.path.join(BASE_DIR, "downloads")
if not os.path.exists(download_path):
    os.makedirs(download_path)

app.mount("/images", StaticFiles(directory=download_path), name="downloads")
print("✅ [9/9] App 設定完成，uvicorn 準備啟動...", flush=True)
# 解決跨域問題 (CORS)，否則 Frontend fetch 會被 block
app.add_middleware(
    CORSMiddleware,
    # 部署後 localhost:5173 會失效，建議加上你 Render 的前端網址
    allow_origins=["http://localhost:5173", "https://local-news-frontend-48mr.onrender.com"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定義數據結構 (Pydantic Model)
class NewsCreate(BaseModel):
    o_title: str
    o_content: str
    t_title: str
    t_content: str
    img_path: Optional[str] = None
    area: str
    source_url: str
    shortened_title: Optional[str] = None
    breaking: int
    status: str


# --- Auth Helpers ---

def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("sub") is None:
            raise HTTPException(status_code=401, detail="無效憑證", headers={"WWW-Authenticate": "Bearer"})
    except JWTError:
        raise HTTPException(status_code=401, detail="無效或已過期的登入憑證", headers={"WWW-Authenticate": "Bearer"})
    return payload.get("sub")


# --- Auth Endpoint ---

@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != ADMIN_USERNAME or not bcrypt.checkpw(form_data.password.encode(), HASHED_PASSWORD):
        raise HTTPException(status_code=401, detail="用戶名或密碼錯誤")
    return {"access_token": create_access_token({"sub": form_data.username}), "token_type": "bearer"}


# --- API Endpoints ---

@app.get("/api/news")
def get_all_news(current_user: str = Depends(get_current_user)):
    rows = db.get_all_news()
    return [{
        "id": r[0],
        "title": r[3],
        "area": r[7],
        "status": r[10],
        "date": r[11],
    } for r in rows]

@app.get("/api/news/pending")
def read_pending_news(current_user: str = Depends(get_current_user)):
    rows = db.get_pending_news()
    result = []
    for r in rows:
        result.append({
            "id": r[0], "o_title": r[1], "o_content": r[2],
            "t_title": r[3], "t_content": r[4], "status": r[8], "img_path": r[5], "area": r[6], "source_url": r[7]
        })
    return result

@app.post("/api/news")
def create_news(news: NewsCreate, current_user: str = Depends(get_current_user)):
    try:
        new_id = db.save_news(
            news.o_title, news.o_content, news.t_title,
            news.t_content, news.img_path, news.area, news.source_url
        )
        return {"status": "success", "id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/news/{news_id}/status")
def change_status(news_id: int, status: str, current_user: str = Depends(get_current_user)):
    db.update_status(news_id, status)
    return {"status": "updated"}

@app.get("/api/news/{news_id}")
def get_one_news(news_id: int, current_user: str = Depends(get_current_user)):
    row = db.get_news_by_id(news_id)
    if not row:
        raise HTTPException(status_code=404, detail="搵唔到呢條新聞")
    return {"id": row[0], "o_title": row[1], "o_content": row[2],
            "t_title": row[3], "t_content": row[5], "area": row[7],
            "img_path": row[6], "source_url": row[7], "shortened_title": row[4], "o_url": row[9]}

@app.put("/api/news/{news_id}")
def update_news(news_id: int, news: NewsCreate, current_user: str = Depends(get_current_user)):
    db.update_news_content(
        news_id, news.o_title, news.o_content,
        news.t_title, news.t_content, news.area,
        news.img_path, news.source_url, news.breaking, news.status
    )
    return {"message": "更新成功"}



@app.post("/api/news/{news_id}/google")
def post_to_google(news_id: int, current_user: str = Depends(get_current_user)):
    row = db.get_news_by_id(news_id)
    if not row:
        raise HTTPException(status_code=404, detail="搵唔到呢條新聞")

    title = row[3]
    content = row[5]

    try:
        print(f"正在發布到 Google: {title}")
        google_link = create_news_doc(title, content)
        return {f"status": "success", "message": "已成功發布到 Google", "link": google_link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"發布到Google失敗: {str(e)}")

@app.post("/api/news/{news_id}/post")
def handle_social_post(news_id: int, current_user: str = Depends(get_current_user)):
    row = db.get_news_by_id(news_id)
    if not row:
        raise HTTPException(status_code=404, detail="搵唔到新聞")

    # 組合貼文內容 (用翻譯後嘅標題同內容)
    post_content = f"{row[3]}\n\n{row[5]}" # Translated Title + Content
    source_url = row[9] # Source URL
    

    # 執行發文
    success, result = post_to_facebook(post_content, link=source_url)
    
    if success:
        db.update_status(news_id, 'POSTED')
        return {"status": "success", "fb_post_id": result}
    else:
        raise HTTPException(status_code=500, detail=f"發布失敗: {result}")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"❌ Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.get("/api/health")
def health_check():
    """
    專門給 UptimeRobot 用的 Endpoint
    不需要 Token 驗證，只回傳 200 OK
    """
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "service": "local-news-backend"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

