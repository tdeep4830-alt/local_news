# api/routes/social.py
from fastapi import APIRouter, HTTPException, Depends
import script.news_db as db
from script.post_to_socialMedia import post_to_facebook
from script.append_to_google_doc import create_news_doc
from api.dependencies import get_current_user  # 引用我哋之前整嘅看更

router = APIRouter(
    prefix="/api/social",
    tags=["Social Media"]
)

@router.post("/facebook/{news_id}")
def handle_facebook_post(news_id: int, current_user: str = Depends(get_current_user)):
    """發布新聞到 Facebook Page"""
    row = db.get_news_by_id(news_id)
    if not row:
        raise HTTPException(status_code=404, detail="搵唔到呢條新聞")

    # 專業建議：喺呢度做埋數據清洗或格式化
    # 假設 row 係一個 Dictionary (如果你喺 db.py 改咗的話)
    title = row.get('translated_title', 'No Title')
    content = row.get('translated_content', '')
    source_url = row.get('source_url', '')
    
    post_content = f"{title}\n\n{content}"
    
    # [Observability] 紀錄發布動作
    print(f"🚀 [Social] 正在為用戶 {current_user} 發布 FB Post: {title[:20]}...")

    success, result = post_to_facebook(post_content, link=source_url)
    
    if success:
        db.update_status(news_id, 'POSTED')
        return {"status": "success", "fb_post_id": result}
    else:
        # [Observability] 失敗時回傳詳細錯誤，方便 Debug
        raise HTTPException(status_code=500, detail=f"Facebook API 報錯: {result}")

@router.post("/google-doc/{news_id}")
def handle_google_doc_post(news_id: int, current_user: str = Depends(get_current_user)):
    """將新聞存檔到 Google Doc"""
    row = db.get_news_by_id(news_id)
    if not row:
        raise HTTPException(status_code=404, detail="搵唔到呢條新聞")

    try:
        title = row.get('translated_title', 'No Title')
        content = row.get('translated_content', '')
        
        print(f"📄 [Social] 正在生成 Google Doc: {title[:20]}...")
        google_link = create_news_doc(title, content)
        
        return {"status": "success", "link": google_link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google API 報錯: {str(e)}")