# services/crawler_service.py
import asyncio
from datetime import datetime
from fastapi.concurrency import run_in_threadpool
from script.parser import pipeline

RSS_URLS = [
    {
        "RSS": "https://www.manchestereveningnews.co.uk/news/?service=rss", 
        "AREA": "Manchester", 
        "SOURCE": "Manchester Evening News", 
        "CLASS_NAME": "Paragraph_paragraph-text__PVKlh "
    },
    {
        "RSS": "https://www.liverpoolecho.co.uk/?service=rss", 
        "AREA": "Liverpool", 
        "SOURCE": "Liverpool Echo", 
        "CLASS_NAME": "Paragraph_paragraph-text__PVKlh"
    },
    {
        "RSS": "https://www.wirralglobe.co.uk/?service=rss", 
        "AREA": "Wirral", 
        "SOURCE": "Wirral Globe", 
        "CLASS_NAME": "article-content"
    }
]

async def run_pipelines():
    print("✅ [Observability] 後台爬蟲服務啟動")
    while True:
        try:
            for rss in RSS_URLS:
                print(f"🚀 正在爬取: {rss['SOURCE']}")
                await run_in_threadpool(
                    pipeline, rss["RSS"], rss["AREA"], rss["SOURCE"], rss["CLASS_NAME"]
                )
            await asyncio.sleep(300)
        except Exception as e:
            print(f"❌ 爬蟲任務出錯: {e}")