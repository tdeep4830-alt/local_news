# services/storage_service.py
import cloudinary
import cloudinary.uploader
from core.config import settings
import requests

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)

def upload_image_to_supabase(image_url: str, file_name: str):
    """從 URL 下載圖片並上傳到 Cloudinary，返回 Public URL"""
    try:
        # 下載圖片到記憶體
        response = requests.get(image_url, timeout=15)
        response.raise_for_status()

        # 上傳到 Cloudinary
        result = cloudinary.uploader.upload(
            response.content,
            public_id=file_name,
            overwrite=True,
            resource_type="image",
        )

        public_url = result.get("secure_url")
        print(f"✅ [Storage] 上傳成功: {public_url}")
        return public_url

    except Exception as e:
        print(f"❌ [Storage] 上傳失敗: {e}")
        return None
