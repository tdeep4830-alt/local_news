from datetime import datetime
from psycopg2.extras import RealDictCursor
import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """獲取資料庫連接"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ 無法連接到資料庫: {e}")
        return None

def init_db():
    """初始化資料庫，建立新聞表"""
    try:
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL 環境變數未設置")
    except Exception as e:
        print(f"❌ 環境變數錯誤: {e}")
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 修正：AUTOINCREMENT 改為 SERIAL, DATETIME 改為 TIMESTAMP
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id SERIAL PRIMARY KEY,
            original_title TEXT,
            original_content TEXT,
            translated_title TEXT,
            shortened_title TEXT,
            translated_content TEXT,
            image_path TEXT,
            area TEXT,
            source TEXT,
            source_url TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP,
            last_updated TIMESTAMP,
            breaking INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ [Observability] Supabase Database 初始化成功")

def add_column_to_news(column_name, column_type="TEXT"):
    """
    動態為 news 表添加新 Column
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
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
    """保存新聞並返回新產生的 ID"""
    conn = get_db_connection()
    # 注意：RealDictCursor 通常用於查詢，Insert 建議用預設 cursor 獲取單個值
    cursor = conn.cursor()
    now = datetime.now()
    
    # 修正 1：佔位符全部改為 %s
    # 修正 2：結尾加入 RETURNING id
    query = '''
        INSERT INTO news (
            original_title, original_content, translated_title, shortened_title, 
            translated_content, image_path, area, source_url, 
            source, created_at, last_updated, breaking
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
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
        # 修正 3：獲取剛剛產生的 ID
        new_id = cursor.fetchone()[0]
        conn.commit()
        return new_id
    except Exception as e:
        print(f"❌ [Observability] 儲存 Supabase 失敗: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_pending_news():
    """獲取所有待審核的新聞"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM news WHERE status = 'PENDING'")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_news_by_id(news_id):
    """根據 ID 獲取新聞詳細資訊"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM news WHERE id = %s", (news_id,))
    row = cursor.fetchone()
    conn.close()
    return row

# 喺你的 DB 檔案入面修改：
def update_news_content(news_id, o_title, o_content, t_title, t_content, img_path, area, source_url, breaking, status):
    """更新新聞內容，確保所有 9 個參數都對齊"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = '''
            UPDATE news 
            SET original_title = %s, 
                original_content = %s, 
                translated_title = %s, 
                translated_content = %s, 
                image_path = %s, 
                area = %s, 
                source_url = %s, 
                breaking = %s,
                last_updated = %s,
                status = %s
            WHERE id = %s
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
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "UPDATE news SET status = %s, last_updated = %s WHERE id = %s",
            (status, datetime.now(), news_id)
        )
        conn.commit()
    finally:
        conn.close()

def get_all_news():
    """獲取所有新聞"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM news")
    rows = cursor.fetchall()
    conn.close()
    return rows

def clear_news():
    """清除所有新聞資料"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("DELETE FROM news")
    conn.commit()
    conn.close()
    print("✅ 所有新聞資料已清除")

def get_id_by_link(source_url):
    """根據來源連結獲取新聞 ID"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id FROM news WHERE source_url = %s", (source_url,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

if __name__ == "__main__":
    add_column_to_news("breaking", "INTEGER DEFAULT 0")  # 如果之前版本冇呢個 column，可以執行一次來添加
    init_db()

