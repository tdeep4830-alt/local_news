import requests
import time
import os
import json
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_to_telegram(news_data: dict):
    """
    將翻譯後的 JSON 內容發送到 Telegram
    """
    title = news_data.get("translated_title", "無標題")
    content = news_data.get("translated_content", "無內文")
    photo = news_data.get("translated_photo", "無圖片")
    news_id = news_data.get("news_id", "無新聞ID")

    # 格式化訊息 (使用 MarkdownV2 或是簡單的 HTML)
    # 這裡用 HTML 格式比較穩定，不易因為特殊字符報錯
    message = f"<b>【香港中文新聞第{news_id}條】</b>\n\n" \
              f"📌 <b>標題:</b> {title}\n\n" \
              f"{content[:1600]}..."  # Telegram 單條訊息上限約 4096 字符，這裡取前 1600 字預防萬一
    if photo:
        message += f"\n\n📷 <b>新聞圖片:</b> {photo}"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        print(f"[{time.strftime('%H:%M:%S')}] 訊息已成功發送至 Telegram")
    except Exception as e:
        print(f"發送 Telegram 失敗: {e}")

# --- 整合邏輯模擬 ---
# news_json = translate_news_with_deepseek(original_title, original_content)
# send_to_telegram(news_json)

if __name__ == "__main__":
    send_to_telegram()