from .translate import translate_news_with_deepseek
from .photo_producer import download_jpg, add_text_to_image_with_background
import requests
import re
import json
import os
from bs4 import BeautifulSoup
from .news_db import save_news
from typing import List


STACK_CAPACITY = 100 # 防止記憶體無限增長

# 模擬 Stack 存放已處理的文章唯一標識符 (Entry ID or Link)
seen_entries_stack: List[str] = []



def process_news_item_thePost(item: dict, area: str, source: str) -> dict:
    result = {}
    result["o_title"] = item.get('title', '')
    result["source_url"] = item.get('link', '') # 記住存低 URL
    
    # 獲取內文
    result["o_content"] = item.get('content', '')
    
    # 翻譯
    translated = translate_news_with_deepseek(result["o_title"], result["o_content"])
    result["t_title"] = translated.get("translated_title", "")
    result["t_content"] = translated.get("translated_content", "")
    result["shortened_title"] = translated.get("shortened_title", "")
    
    # 圖片抓取修正：建議用之前討論過嘅 get_image_url 邏輯
    # 如果堅持用 links，先 check 長度
    download_jpg(item.get('photo', ''), item.get('title', ''))

    photo_name = re.sub(r'[\\/*?:"<>|\s]+', "_", str(item.get('title', '')))
    downloads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "downloads")
    add_text_to_image_with_background(os.path.join(downloads_dir, f"{photo_name}.jpg"), result["shortened_title"], photo_name, breaking=0, source=source)
    result["image"] = f"{photo_name}_with_title.jpg"
    result["area"] = area
    result["source"] = source

    return result


def fetch_news_from_thePost(url: str) -> list:
    global seen_entries_stack
    new_links = [] # 修正 1：將收集結果嘅 List 放喺 for 迴圈外面
    base_url = "https://www.livpost.co.uk" # 用嚟拼接相對路徑
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # 直接尋找所有 class 為 c-card__media 的 <a> 標籤
        media_tags = soup.find_all("a", class_="c-card__media")

        for tag in media_tags:
            link = tag.get("href")
            
            if link:
                # 處理相對路徑
                full_url = base_url + link if link.startswith('/') else link
                
                # 檢查是否已經處理過
                if full_url not in seen_entries_stack:
                    new_links.append(full_url) # 修正 2：加落出面嗰個 List
                    seen_entries_stack.append(full_url)

        return new_links

    except Exception as e:
        print(f"從 The Post 獲取新聞內容時發生錯誤: {e}")
        return []

def parse_news_content_for_livpost(url: str) -> str:
    html_content = requests.get(url).text
    soup = BeautifulSoup(html_content, 'html.parser')
    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        data = json.loads(script.string)
        title = data.get("headline", "")
        photo_data = data.get('image', {})
        photo_image_url = photo_data.get('url', '')
        content_div = soup.find("div", class_="c-content")
        if content_div:
            paragraphs = content_div.find_all("p")
            content = "\n".join([p.get_text(strip=True) for p in paragraphs])
        else:
            content = ""

    return {"title": title, "photo": photo_image_url, "content": content, "link": url}

def thePost_pipeline():
    news_items = fetch_news_from_thePost("https://www.livpost.co.uk/")
    for link in news_items:
        news = parse_news_content_for_livpost(link)
        processed = process_news_item_thePost(news, area="liverpool", source="thePost")
        try:
            save_news(processed)
            print(f"已保存新聞: {processed['t_title']}")
        except Exception as e:
            print(f"保存新聞時發生錯誤: {e}")