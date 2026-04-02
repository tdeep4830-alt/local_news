# api/routes/social.py
from fastapi import APIRouter, HTTPException, Depends
import script.news_db as db
from script.post_to_socialMedia import post_to_facebook, post_to_instagram
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

    title = row[3] or 'No Title'
    content = row[5] or ''
    source_url = row[9] or ''
    
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

@router.post("/instagram/{news_id}")
def handle_instagram_post(news_id: int, current_user: str = Depends(get_current_user)):
    """發布新聞到 Instagram"""
    row = db.get_news_by_id(news_id)
    if not row:
        raise HTTPException(status_code=404, detail="搵唔到呢條新聞")

    title = row[3] or 'No Title'
    content = row[5] or ''
    message = f"{title}\n\n{content}"
    image_url = row[6]
    if not image_url:
        raise HTTPException(status_code=400, detail="呢條新聞冇圖片，無法發布到 Instagram")

    print(f"📸 [Social] 正在為用戶 {current_user} 發布 IG Post: {title[:20]}...")
    print(f"📸 [Social] image_url: {repr(image_url)}")
    success, result = post_to_instagram(message, image_url)

    if success:
        db.update_status(news_id, 'POSTED')
        return {"status": "success", "ig_post_id": result}
    else:
        raise HTTPException(status_code=500, detail=f"Instagram API 報錯: {result}")

@router.post("/google-doc/{news_id}")
def handle_google_doc_post(news_id: int, current_user: str = Depends(get_current_user)):
    """將新聞存檔到 Google Doc"""
    row = db.get_news_by_id(news_id)
    if not row:
        raise HTTPException(status_code=404, detail="搵唔到呢條新聞")

    try:
        title = row[3] or 'No Title'
        content = row[5] or ''
        image_url = row[6] or ""
        
        print(f"📄 [Social] 正在生成 Google Doc: {title[:20]}...")
        google_link = create_news_doc(title, content, image_url)
        
        return {"status": "success", "link": google_link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google API 報錯: {str(e)}")
    