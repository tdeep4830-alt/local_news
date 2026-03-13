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


STACK_CAPACITY = 100 # 防止記憶體無限增長

# 模擬 Stack 存放已處理的文章唯一標識符 (Entry ID or Link)
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

        # RSS 項目通常按時間倒序排列，我們由舊到新處理或直接遍歷
        for entry in reversed(feed.entries):
            entry_id = entry.get(entry.link, "")

            # 檢查是否已在 Stack 中 (重複檢查)
            if entry_id not in seen_entries_stack:
                # 執行你的邏輯，例如推送到通知、存入資料庫等
                new_items.append(entry)

                # Push 到 Stack
                seen_entries_stack.append(entry_id)
                new_items_found_count += 1

                # 維持 Stack 長度，移除最舊的數據 (類似 Fixed-size Stack)
                if len(seen_entries_stack) > STACK_CAPACITY:
                    seen_entries_stack.pop(0)

        if new_items_found_count == 0:
            print("暫無新更新。")
        else:
            print(f"本次更新了 {new_items_found_count} 條新聞。")

        return new_items

    except Exception as e:
        print(f"發生錯誤: {e}")

@timer_decorator
def fetch_news_content(url: str) -> str:
    """
    根據 URL 下載網頁並提取指定 class 的內文
    """
    try:
        # 1. 發送請求，加入 User-Agent 模擬瀏覽器，避免被網站封鎖
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        # 檢查請求是否成功
        response.raise_for_status()
        
        # 2. 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 3. 尋找所有指定 class 的元素
        # 你提到的 class 是 "Paragraph_paragraph-text__PVKlh"
        paragraphs = soup.find_all(class_="Paragraph_paragraph-text__PVKlh")
        
        # 4. 提取文字並合併
        content = "\n".join([p.get_text(strip=True) for p in paragraphs])
        
        return content

    except requests.exceptions.RequestException as e:
        print(f"下載網頁失敗 ({url}): {e}")
        return ""
    except Exception as e:
        print(f"解析內容時發生錯誤: {e}")
        return ""

def process_news_item(item: dict, area: str, source: str) -> dict:
    result = {}
    result["o_title"] = item.get('title', '')
    result["source_url"] = item.get('link', '') # 記住存低 URL
    
    # 獲取內文
    result["o_content"] = fetch_news_content(result["source_url"])
    
    # 翻譯
    translated = translate_news_with_deepseek(result["o_title"], result["o_content"])
    result["t_title"] = translated.get("translated_title", "")
    result["t_content"] = translated.get("translated_content", "")
    result["shortened_title"] = translated.get("shortened_title", "")
    
    # 圖片抓取修正：建議用之前討論過嘅 get_image_url 邏輯
    # 如果堅持用 links，先 check 長度
    download_jpg(item.links[1]['href'], item.get('title', ''))
    photo_name = re.sub(r'[\\/*?:"<>|\s]+', "_", str(item.get('title', '')))
    downloads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "downloads")
    add_text_to_image_with_background(os.path.join(downloads_dir, f"{photo_name}.jpg"), result["shortened_title"], photo_name, breaking=0, source=source)
    result["image"] = f"{photo_name}_with_title.jpg"
    result["area"] = area
    result["source"] = source

    return result

def echo_pipeline():
    news_items = fetch_and_check_echo_rss()
    for item in news_items:  # 只處理最新的 3 條新聞，避免一次處理太多
        processed = process_news_item(item, area="liverpool", source="liverpoolecho")
        try:
            save_news(processed)
            print(f"已保存新聞: {processed['t_title']}")
        except Exception as e:
            print(f"保存新聞時發生錯誤: {e}")

if __name__ == "__main__":
    while True:
        echo_pipeline()
        print("服務已啟動，每五分鐘將自動執行一次...")
        schedule.run_pending()
        time.sleep(300)