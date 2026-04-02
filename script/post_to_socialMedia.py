import os
import requests
import logging
from dotenv import load_dotenv
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
from news_db import get_news_by_id, update_status
from fastapi import FastAPI, HTTPException 
from fastapi.middleware.cors import CORSMiddleware
import time

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

def post_to_instagram(message: str, image_url: str):
    """
    呼叫 Instagram Graph API 分兩步發布貼文
    """
    user_id = os.getenv("IG_USER_ID")
    access_token = os.getenv("IG_ACCESS_TOKEN")
    if not access_token:
        logger.error("❌ 環境變數錯誤: IG_ACCESS_TOKEN 未設定")
        return False, "IG_ACCESS_TOKEN 未設定"
    
    # --- 第一步：建立媒體容器 (Create Container) ---
    # 注意：通常使用 graph.facebook.com，版本建議用最新 v21.0
    container_url = f"https://graph.instagram.com/v21.0/{user_id}/media"
    
    payload = {
        "image_url": image_url,
        "media_type": "IMAGE",
        "caption": message,
        "access_token": access_token
    }

    try:
        # 1. 請求建立容器
        logger.info(f"🔍 container_url: {container_url}")
        logger.info(f"🔍 image_url: {repr(image_url)}")
        logger.info(f"🔍 user_id: {repr(user_id)}")
        response = requests.post(container_url, params=payload)
        logger.info(f"🔍 request url: {response.request.url}")
        res_data = response.json()

        if response.status_code != 200:
            logger.error(f"❌ 建立容器失敗: {res_data}")
            return False, res_data
        
        creation_id = res_data.get('id')
        logger.info(f"📦 容器建立成功，ID: {creation_id}")

        # --- 第二步：正式發布媒體 (Publish Media) ---
        # IG 建議等幾秒確保圖片處理完成
        time.sleep(5) 
        
        publish_url = f"https://graph.instagram.com/v21.0/{user_id}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": access_token
        }

        publish_response = requests.post(publish_url, params=publish_payload)
        publish_data = publish_response.json()

        if publish_response.status_code == 200:
            final_post_id = publish_data.get('id')
            logger.info(f"✅ Instagram 正式發文成功! 貼文 ID: {final_post_id}")
            return True, final_post_id
        else:
            logger.error(f"❌ 正式發布失敗: {publish_data}")
            return False, publish_data

    except Exception as e:
        logger.error(f"❌ 網絡或執行失敗: {str(e)}")
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

if __name__ == "__main__":
    message = "測試貼文內容"
    photo_url = "https://iwmzydqwcnwmaauegooz.supabase.co/storage/v1/object/public/images/f93a7910-e1eb-4240-b571-079916ba9e55_Tributes_pour_in_as_beautiful_man_dies_after_brutal_attack_outside_Irlam_pub.jpg"
    post_to_instagram(message, photo_url)