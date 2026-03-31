from datetime import datetime
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load .env from project root (works both when imported and run directly)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """獲取資料庫連接"""
    if not DATABASE_URL:
        print("❌ 環境變數錯誤: DATABASE_URL 環境變數未設定")
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ 無法連接到資料庫: {e}")
        return None

def init_db():
    """初始化資料庫，建立新聞表"""
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()
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

def save_news(data: dict):
    """保存新聞並返回新產生的 ID"""
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    now = datetime.now()
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
        new_id = cursor.fetchone()[0]
        conn.commit()
        print(f"✅ 新聞已儲存，ID: {new_id}")
        return new_id
    except Exception as e:
        print(f"❌ [Observability] 儲存 Supabase 失敗: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def get_pending_news():
    """獲取所有待審核的新聞"""
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM news WHERE status = 'PENDING'")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_news_by_id(news_id):
    """根據 ID 獲取新聞詳細資訊"""
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM news WHERE id = %s", (news_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def update_news_content(news_id, o_title, o_content, t_title, t_content, img_path, area, source_url, breaking, status):
    """更新新聞內容"""
    conn = get_db_connection()
    if conn is None:
        return
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
        cursor.execute(query, (
            o_title, o_content, t_title, t_content,
            img_path, area, source_url,
            1 if breaking else 0,
            datetime.now(), status, news_id
        ))
        conn.commit()
        print(f"✅ DB Updated: ID {news_id}")
    except Exception as e:
        print(f"❌ DB Update Error: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_status(news_id, status):
    """更新新聞狀態"""
    conn = get_db_connection()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE news SET status = %s, last_updated = %s WHERE id = %s",
            (status, datetime.now(), news_id)
        )
        conn.commit()
    except Exception as e:
        print(f"❌ update_status Error: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_all_news():
    """獲取所有新聞"""
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM news ORDER BY created_at DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def clear_news():
    """清除所有新聞資料"""
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    cursor.execute("DELETE FROM news")
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ 所有新聞資料已清除")

def get_id_by_link(source_url):
    """根據來源連結獲取新聞 ID"""
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM news WHERE source_url = %s", (source_url,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None

def get_news_by_date(news_date):
    """根據日期獲取新聞"""
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM news WHERE created_at::date = %s", (news_date,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_news_count_by_month(month_str):
    """返回指定月份每日新聞數量，month_str 格式: '2026-03'"""
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT created_at::date AS date, COUNT(*) AS count
        FROM news
        WHERE TO_CHAR(created_at, 'YYYY-MM') = %s
        GROUP BY created_at::date
        ORDER BY date
    """, (month_str,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def reject_news(news_id):
    """拒絕新聞"""
    conn = get_db_connection()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE news SET status = 'rejected' WHERE id = %s", (news_id,))
        conn.commit()
        print(f"✅ News Rejected: ID {news_id}")
    except Exception as e:
        print(f"❌ Reject News Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
