# api/routes/news.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
import script.news_db as db
# 這裡假設你把 get_current_user 放在一個公用地方，或暫時從 main import
# 建議之後移到 api/dependencies.py
from api.dependencies import get_current_user

router = APIRouter(
    prefix="/api/news",
    tags=["News"] # 這會讓你的 Swagger UI (docs) 自動分類，非常專業
)

# 定義數據結構 (原本在 main.py 的 Pydantic Model)
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

# --- 把 API 搬過來，注意：路徑會自動加上 prefix "/api/news" ---

@router.get("/") # 實際路徑：/api/news/
def get_all_news(current_user: str = Depends(get_current_user)):
    rows = db.get_all_news()
    # 這裡建議改用 Dict 存取，增加 Observability
    return [{
        "id": r[0],
        "title": r[3],
        "area": r[7],
        "status": r[10],
        "date": r[11],
    } for r in rows]

@router.get("/pending") # 實際路徑：/api/news/pending
def read_pending_news(current_user: str = Depends(get_current_user)):
    rows = db.get_pending_news()
    return [{
        "id": r[0], "o_title": r[1], "o_content": r[2],
        "t_title": r[3], "t_content": r[4], "status": r[8], 
        "img_path": r[5], "area": r[6], "source_url": r[7]
    } for r in rows]

@router.post("/")
def create_news(news: NewsCreate, current_user: str = Depends(get_current_user)):
    try:
        new_id = db.save_news(news.model_dump()) # 專業寫法：用 model_dump()
        return {"status": "success", "id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{news_id}")
def get_one_news(news_id: int, current_user: str = Depends(get_current_user)):
    row = db.get_news_by_id(news_id)
    if not row:
        raise HTTPException(status_code=404, detail="搵唔到呢條新聞")
    # 這裡也要對應你的 DB 結構
    return {"id": row[0], "o_title": row[1], "t_title": row[3], "t_content": row[5], "img_path": row[6], "area": row[7], "o_url": row[9], "status": row[10]}


@router.put("/{news_id}")
def update_news(news_id: int, news: NewsCreate, current_user: str = Depends(get_current_user)):

    db.update_news_content(
        news_id, news.o_title, news.o_content,
        news.t_title, news.t_content, news.area,
        news.img_path, news.source_url, news.breaking, news.status
    )

    return {"message": "更新成功"}



