# main.py
import sys, os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

# 引用你拆出去的模組
from core.config import settings
from services.crawler_service import run_pipelines
from script.news_db import init_db
# 這裡稍後會加入 API Router
from api.routes import news, auth, social


@asynccontextmanager
async def lifespan(app: FastAPI):
    # [Infra] 初始化資料庫
    try:
        init_db()
        print("✅ [Observability] DB 初始化成功")
    except Exception as e:
        print(f"❌ DB 初始化失敗: {e}")

    # [Infra] 啟動爬蟲工人
    crawler_task = asyncio.create_task(run_pipelines())
    yield
    crawler_task.cancel()

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)


# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 部署時再縮小範圍
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news.router)
app.include_router(auth.router) # 這裡會自動加上 prefix "/api/auth" 和 tags "Authentication"
app.include_router(social.router)

# 健康檢查 (給 UptimeRobot)
@app.get("/api/health")
def health_check():
    return {"status": "online"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
