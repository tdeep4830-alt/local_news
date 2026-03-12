import os
import requests
import logging
from dotenv import load_dotenv
from news_db import get_news_by_id, update_status
from fastapi import FastAPI, HTTPException 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

# 設定簡單嘅 Logging (為之後嘅 Observability 鋪路)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def post_to_facebook(message: str, link: str = None, photo_url: str = None):
    """
    呼叫 Facebook Graph API 發布貼文
    """
    page_id = os.getenv("FB_PAGE_ID")
    access_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    url = f"https://graph.facebook.com/v25.0/{page_id}/feed"
    
    
    payload = {
        "message": message,
        "access_token": access_token
    }
    if link:
        payload["link"] = link

    if photo_url:
        payload["image_url"] = photo_url

    try:
        response = requests.post(url, data=payload)
        response_data = response.json()
        
        if response.status_code == 200:
            logger.info(f"✅ Facebook 發文成功: {response_data.get('id')}")
            return True, response_data.get('id')
        else:
            logger.error(f"❌ Facebook API 報錯: {response_data}")
            return False, response_data.get('error', {}).get('message')
            
    except Exception as e:
        logger.error(f"❌ 網絡連線失敗: {str(e)}")
        return False, str(e)

def post_to_instagram(message: str, image_url: str = None):
    """
    呼叫 Instagram Graph API 發布貼文
    """
    user_id = os.getenv("IG_USER_ID")
    access_token = os.getenv("IG_ACCESS_TOKEN")
    url = f"https://graph.instagram.com/v12.0/{user_id}/media"

    payload = {
        "caption": message,
        "access_token": access_token
    }
    if image_url:
        payload["image_url"] = image_url

    try:
        response = requests.post(url, data=payload)
        response_data = response.json()

        if response.status_code == 200:
            logger.info(f"✅ Instagram 發文成功: {response_data.get('id')}")
            return True, response_data.get('id')
        else:
            logger.error(f"❌ Instagram API 報錯: {response_data}")
            return False, response_data.get('error', {}).get('message')

    except Exception as e:
        logger.error(f"❌ 網絡連線失敗: {str(e)}")
        return False, str(e)

def post_to_thread(message: str, link: str = None):
    """
    呼叫 Thread API 發布貼文
    """
    user_id = os.getenv("THREAD_USER_ID")
    access_token = os.getenv("THREAD_ACCESS_TOKEN")
    url = f"https://api.threads.com/v1/{user_id}/media"

    payload = {
        "message": message,
        "access_token": access_token
    }
    if link:
        payload["link"] = link

    try:
        response = requests.post(url, data=payload)
        response_data = response.json()

        if response.status_code == 200:
            logger.info(f"✅ Thread 發文成功: {response_data.get('id')}")
            return True, response_data.get('id')
        else:
            logger.error(f"❌ Thread API 報錯: {response_data}")
            return False, response_data.get('error', {}).get('message')

    except Exception as e:
        logger.error(f"❌ 網絡連線失敗: {str(e)}")
        return False, str(e)

# 修改原本嘅 Post Endpoint
@app.post("/api/news/{news_id}/post")
def handle_social_post(news_id: int):
    row = get_news_by_id(news_id)
    if not row:
        raise HTTPException(status_code=404, detail="搵唔到新聞")

    # 組合貼文內容 (用翻譯後嘅標題同內容)
    post_content = f"{row[3]}\n\n{row[4]}" # Translated Title + Content
    source_url = row[7] # Source URL

    # 執行發文
    success, result = post_to_facebook(post_content, link=source_url)
    
    if success:
        update_status(news_id, 'POSTED')
        return {"status": "success", "fb_post_id": result}
    else:
        raise HTTPException(status_code=500, detail=f"發布失敗: {result}")
    
if __name__ == "__main__":
    post_to_facebook("測試貼文內容", link="https://www.example.com")