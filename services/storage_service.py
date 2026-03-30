# services/storage_service.py
from supabase import create_client, Client
from core.config import settings
import uuid
import requests

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def upload_image_to_supabase(image_url: str, file_name: str):
    """從 URL 下載圖片並上傳到 Supabase，返回 Public URL"""
    try:
        bucket_name = "images"

        # 1. 從 URL 下載圖片到記憶體
        response = requests.get(image_url, timeout=15)
        response.raise_for_status()
        image_bytes = response.content

        # 2. 上傳到 Supabase
        unique_name = f"{uuid.uuid4()}_{file_name}.jpg"
        supabase.storage.from_(bucket_name).upload(
            path=unique_name,
            file=image_bytes,
            file_options={"content-type": "image/jpeg"}
        )

        # 3. 獲取 Public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(unique_name)

        print(f"✅ [Storage] 上傳成功: {public_url}")
        return public_url

    except Exception as e:
        print(f"❌ [Storage] 上傳失敗: {e}")
        return None