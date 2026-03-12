import feedparser
import schedule
import time
from typing import List

RSS_URL = "https://www.liverpoolecho.co.uk/?service=rss"
STACK_CAPACITY = 100  # 防止記憶體無限增長

# 模擬 Stack 存放已處理的文章唯一標識符 (Entry ID or Link)
seen_entries_stack: List[str] = []

def fetch_and_check_rss():
    global seen_entries_stack
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 正在檢查更新...")
    
    try:
        feed = feedparser.parse(RSS_URL)
        new_items = []
        new_items_found_count = 0

        # RSS 項目通常按時間倒序排列，我們由舊到新處理或直接遍歷
        for entry in reversed(feed.entries):
            entry_id = entry.get('id', entry.link)

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


# 定時任務設定
# schedule.every(1).hours.do(fetch_and_check_rss)

if __name__ == "__main__":
    # 啟動時先執行一次
    results = fetch_and_check_rss()
    for result in results:
        print(f"新文章: {result}")

    # print("服務已啟動，每小時將自動執行一次...")
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)