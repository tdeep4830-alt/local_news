import requests
from bs4 import BeautifulSoup
import feedparser
import time
from typing import List
from .translate import translate_news_with_deepseek
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from .news_db import save_news
from .photo_producer import download_jpg, add_text_to_image_with_background
import schedule
import json
import re

STACK_CAPACITY = 100 

seen_entries_stack: List[str] = []

def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"DEBUG: {func.__name__} 用了 {time.time() - start:.2f} 秒")
        return result
    return wrapper

@timer_decorator
def fetch_and_check_echo_rss():
    global seen_entries_stack
    RSS_URL = "https://www.liverpoolecho.co.uk/?service=rss"
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 正在檢查更新...")
    
    try:
        r = requests.get(RSS_URL, timeout=10)
        feed = feedparser.parse(r.text)
        new_items = []
        new_items_found_count = 0

        for entry in reversed(feed.entries):
            # 修正 1：正確獲取唯一 ID
            entry_id = entry.get('id', entry.link)

            if entry_id not in seen_entries_stack:
                new_items.append(entry)
                seen_entries_stack.append(entry_id)
                new_items_found_count += 1

                if len(seen_entries_stack) > STACK_CAPACITY:
                    seen_entries_stack.pop(0)

        if new_items_found_count == 0:
            print("暫無新更新。")
        else:
            print(f"本次更新了 {new_items_found_count} 條新聞。")

        return new_items

    except Exception as e:
        print(f"檢查 RSS 發生錯誤: {e}")
        return [] # 確保出錯時回傳空 list

@timer_decorator
def fetch_news_content(url: str) -> str:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all(class_="Paragraph_paragraph-text__PVKlh")
        content = "\n".join([p.get_text(strip=True) for p in paragraphs])
        
        return content

    except Exception as e:
        print(f"解析內容時發生錯誤: {e}")
        return ""

def process_news_item(item: dict, area: str, source: str) -> dict:
    result = {}
    result["o_title"] = item.get('title', '')
    result["source_url"] = item.get('link', '') 
    
    result["o_content"] = fetch_news_content(result["source_url"])
    
    translated = translate_news_with_deepseek(result["o_title"], result["o_content"])
    result["t_title"] = translated.get("translated_title", "")
    result["t_content"] = translated.get("translated_content", "")
    result["shortened_title"] = translated.get("shortened_title", "")
    
    # 修正 2：先建立安全的 photo_name，然後統一使用
    photo_name = re.sub(r'[\\/*?:"<>|\s]+', "_", str(result["o_title"]))
    
    # 確保 links 存在且有足夠長度避免 IndexError
    image_url = item.links[1]['href'] if hasattr(item, 'links') and len(item.links) > 1 else ""
    
    if image_url:
        download_jpg(image_url, photo_name) # 用乾淨的檔名下載
        downloads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "downloads")
        add_text_to_image_with_background(os.path.join(downloads_dir, f"{photo_name}.jpg"), result["shortened_title"], photo_name, breaking=0, source=source)
        result["image"] = f"{photo_name}_with_title.jpg"
    else:
        result["image"] = ""
        
    result["area"] = area
    result["source"] = source

    return result

def echo_pipeline():
    news_items = fetch_and_check_echo_rss()
    for item in news_items: 
        try:
            processed = process_news_item(item, area="liverpool", source="liverpoolecho")
            save_news(processed)
            print(f"✅ 已保存新聞: {processed['t_title']}")
        except Exception as e:
            print(f"❌ 處理或保存新聞時發生錯誤: {e}")

if __name__ == "__main__":
    print("服務準備啟動...")
    # 第一次啟動先跑一次，避免要白等 5 分鐘
    echo_pipeline() 
    
    # 修正 3：正確定義排程
    schedule.every(5).minutes.do(echo_pipeline)
    print("排程已設定，每五分鐘將自動執行一次...")
    
    while True:
        schedule.run_pending()
        time.sleep(1) # 只 sleep 1 秒避免 CPU 空轉，時間管理交畀 schedule