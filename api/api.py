# main.py
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
import sys, os
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from dotenv import load_dotenv


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from script.append_to_google_doc import create_news_doc
import script.news_db as db
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SECRET_KEY     = os.getenv("JWT_SECRET_KEY")
ALGORITHM      = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

oauth2_scheme   = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
HASHED_PASSWORD = bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt())

app = FastAPI()

app.mount("/images", StaticFiles(directory="/Users/tobychunyu/Desktop/Deep/local_news/downloads"), name="downloads")

# 解決跨域問題 (CORS)，否則 Frontend fetch 會被 block
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # 填返你 Frontend 粒 Port
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

@app.post("/api/news/{news_id}/post")
def post_to_social_media(news_id: int, current_user: str = Depends(get_current_user)):
    row = db.get_news_by_id(news_id)
    if not row:
        raise HTTPException(status_code=404, detail="搵唔到呢條新聞")

    title = row[3]
    content = row[4]

    try:
        print(f"正在發布到社交媒體: {title}")
        db.update_status(news_id, 'POSTED')
        return {"status": "success", "message": "已成功發布到社交媒體"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"發布失敗: {str(e)}")

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

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"❌ Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
