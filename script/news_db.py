import sqlite3
from datetime import datetime

def init_db():
    """初始化資料庫，建立新聞表"""
    conn = sqlite3.connect('news_system.db')
    cursor = conn.cursor()
    
    # 建立一個 Table，包含原文、翻譯、狀態和時間戳
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_title TEXT,
            original_content TEXT,
            translated_title TEXT,
            shortened_title TEXT,
            translated_content TEXT,
            image_path TEXT,
            area TEXT,
            source TEXT,
            source_url TEXT,
            status TEXT DEFAULT 'PENDING', -- 狀態：PENDING, APPROVED, POSTED, REJECTED
            created_at DATETIME,
            last_updated DATETIME,
            breaking INTEGER DEFAULT 0  -- 0 為 False, 1 為 True
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Database 初始化成功")

def add_column_to_news(column_name, column_type="TEXT"):
    """
    動態為 news 表添加新 Column
    """
    conn = sqlite3.connect('./news_system.db')
    cursor = conn.cursor()
    try:
        # SQLite 唔支援一次加多個 Column，所以要分開做
        cursor.execute(f"ALTER TABLE news ADD COLUMN {column_name} {column_type}")
        conn.commit()
        print(f"✅ 成功添加 Column: {column_name}")
    except sqlite3.OperationalError:
        print(f"⚠️ Column {column_name} 可能已經存在，跳過更新。")
    finally:
        conn.close()

def save_news(data: dict):
    """改為接收 Dictionary，擴展性更好"""
    conn = sqlite3.connect('./news_system.db')
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    # 修正：確保 columns 同 values 數量完全對應 (11個)
    query = '''
        INSERT INTO news (
            original_title, original_content, translated_title, shortened_title, 
            translated_content, image_path, area, source_url, 
            source, created_at, last_updated, breaking
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    params = (
        data.get("o_title"),
        data.get("o_content"),
        data.get("t_title"),
        data.get("shortened_title"),
        data.get("t_content"),
        data.get("image"),
        data.get("area"),
        data.get("source_url"),
        data.get("source"), 
        now,
        now,
        data.get("breaking", 0)
    )
    
    try:
        cursor.execute(query, params)
        last_id = cursor.lastrowid
        conn.commit()
        return last_id
    except Exception as e:
        print(f"❌ 儲存資料庫失敗: {e}")
        return None
    finally:
        conn.close()

def get_pending_news():
    """獲取所有待審核的新聞"""
    conn = sqlite3.connect('./news_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM news WHERE status = 'PENDING'")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_news_by_id(news_id):
    """根據 ID 獲取新聞詳細資訊"""
    conn = sqlite3.connect('./news_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM news WHERE id = ?", (news_id,))
    row = cursor.fetchone()
    conn.close()
    return row

# 喺你的 DB 檔案入面修改：
def update_news_content(news_id, o_title, o_content, t_title, t_content, img_path, area, source_url, breaking, status):
    """更新新聞內容，確保所有 9 個參數都對齊"""
    conn = sqlite3.connect('./news_system.db')
    try:
        cursor = conn.cursor()
        query = '''
            UPDATE news 
            SET original_title = ?, 
                original_content = ?, 
                translated_title = ?, 
                translated_content = ?, 
                image_path = ?, 
                area = ?, 
                source_url = ?, 
                breaking = ?,
                last_updated = ?,
                status = ?
            WHERE id = ?
        '''
        # 參數順序必須同 SQL query 入面嘅問號完全一致
        cursor.execute(query, (
            o_title, 
            o_content, 
            t_title, 
            t_content, 
            img_path, 
            area, 
            source_url, 
            1 if breaking else 0, 
            datetime.now(), 
            status,
            news_id
        ))
        conn.commit()
        print(f"✅ DB Updated: ID {news_id}")
    except Exception as e:
        print(f"❌ DB Update Error: {e}")
    finally:
        conn.close()

def update_status(news_id, status):
    """更新新聞狀態"""
    conn = sqlite3.connect('./news_system.db')
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE news SET status = ?, last_updated = ? WHERE id = ?",
            (status, datetime.now(), news_id)
        )
        conn.commit()
    finally:
        conn.close()

def get_all_news():
    """獲取所有新聞"""
    conn = sqlite3.connect('./news_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM news")
    rows = cursor.fetchall()
    conn.close()
    return rows

def clear_news():
    """清除所有新聞資料"""
    conn = sqlite3.connect('./news_system.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM news")
    conn.commit()
    conn.close()
    print("✅ 所有新聞資料已清除")

def get_id_by_link(source_url):
    """根據來源連結獲取新聞 ID"""
    conn = sqlite3.connect('./news_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM news WHERE source_url = ?", (source_url,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

if __name__ == "__main__":
    add_column_to_news("breaking", "INTEGER DEFAULT 0")  # 如果之前版本冇呢個 column，可以執行一次來添加
    init_db()

