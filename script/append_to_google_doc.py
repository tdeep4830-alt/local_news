from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import sys
import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.config import settings


# 設定 API 權限範圍：需要讀寫 Drive 和 Docs
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

_DIR = os.path.dirname(os.path.abspath(__file__))
_TOKEN_PATH = os.path.join(_DIR, 'token.json')
_CREDS_PATH = os.path.join(_DIR, 'credentials.json')

def get_drive_service():
    # 從 Render 環境變數讀取
    creds = Credentials(
        token=None, # 初始設為 None，靠 refresh_token 換取
        refresh_token=settings.GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/drive.file']
    )

    # 如果 token 過期，自動重新整理
    if not creds.valid:
        creds.refresh(Request())
    
    return build('drive', 'v3', credentials=creds)

def get_google_services():
    """驗證並獲取 Drive 和 Docs 服務"""
    creds = None
    if os.path.exists(_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(_TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(_CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(_TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('docs', 'v1', credentials=creds), build('drive', 'v3', credentials=creds)

def get_authenticated_service():
    """統一獲取服務的入口，優先使用環境變數"""

    # 嘗試從環境變數讀取 (Render 環境)
    if settings.GOOGLE_REFRESH_TOKEN:
        print(f"🔑 [Google] 使用環境變數 refresh token (長度: {len(settings.GOOGLE_REFRESH_TOKEN)})")
        print(f"🔑 [Google] CLIENT_ID: {settings.GOOGLE_CLIENT_ID[:20] if settings.GOOGLE_CLIENT_ID else '未設定'}...")
        creds = Credentials(
            token=None,
            refresh_token=settings.GOOGLE_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=SCOPES
        )
    # 否則從本地 token.json 讀取 (開發環境)
    elif os.path.exists(_TOKEN_PATH):
        print(f"🔑 [Google] 使用本地 token.json")
        creds = Credentials.from_authorized_user_file(_TOKEN_PATH, SCOPES)
    else:
        print(f"🔑 [Google] 冇 token，跑 OAuth flow")
        flow = InstalledAppFlow.from_client_secrets_file(_CREDS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(_TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    # 確保 Token 有效
    print(f"🔍 [Google] creds.valid={creds.valid}, expired={creds.expired}, has_refresh={bool(creds.refresh_token)}")
    if not creds.valid:
        if creds.refresh_token:
            print(f"🔄 [Google] 嘗試 refresh token...")
            creds.refresh(Request())
            print(f"✅ [Google] Token refresh 成功")
        else:
            print(f"❌ [Google] 冇 refresh token，無法取得有效憑證")

    return build('docs', 'v1', credentials=creds), build('drive', 'v3', credentials=creds)

def get_or_create_date_folder(drive_service, date: str) -> str:
    """搵或建立當日日期的 Google Drive Folder，返回 folder_id"""
    # 搜尋同名 folder
    query = f"name='{date}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get("files", [])

    if folders:
        folder_id = folders[0]["id"]
        print(f"📁 [Google] 找到現有 Folder: {date} (ID: {folder_id})")
    else:
        folder_metadata = {
            "name": date,
            "mimeType": "application/vnd.google-apps.folder"
        }
        folder = drive_service.files().create(body=folder_metadata, fields="id").execute()
        folder_id = folder.get("id")
        print(f"📁 [Google] 新建 Folder: {date} (ID: {folder_id})")

    return folder_id


def create_news_doc(title: str, content: str, image_url: str):
    """
    建立一個新的 Google Doc 並插入標題、圖片與內容
    """
    docs_service, drive_service = get_authenticated_service()
    date = datetime.datetime.now().strftime("%Y-%m-%d")

    try:
        # 1. 搵或建立當日 Folder
        folder_id = get_or_create_date_folder(drive_service, date)

        # 2. 透過 Drive API 建立一個空白的 Google Doc，放入 Folder
        file_metadata = {
            'name': f"{date} - 新聞：{title}",
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [folder_id]
        }
        doc_file = drive_service.files().create(body=file_metadata, fields='id').execute()
        document_id = doc_file.get('id')
        print(f"✅ 已建立新文件，ID: {document_id}")


        # 2. 準備寫入內容的 Requests
        # Google Docs API 使用「倒序插入」或計算索引，這裡按順序構建
        requests = [
            # 插入標題
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': f"{title}\n\n"
                }
            },
            # 設定標題樣式 (Heading 1)
            {
                'updateParagraphStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(title) + 1},
                    'paragraphStyle': {'namedStyleType': 'HEADING_1'},
                    'fields': 'namedStyleType'
                }
            },
            
            # 插入圖片
            {
                'insertInlineImage': {
                    'location': {'index': len(title) + 3},
                    'uri': image_url,
                    'objectSize': {
                        'width': {'magnitude': 400, 'unit': 'PT'},
                        'height': {'magnitude': 300, 'unit': 'PT'}
                    }
                }
            },
            # 插入內文
            {
                'insertText': {
                    'location': {'index': len(title) + 4},
                    'text': f"\n\n{content}"
                }
            }


        ]

        # 3. 執行批次更新
        docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
        
        doc_url = f"https://docs.google.com/document/d/{document_id}/edit"
        print(f"🚀 新聞內容已成功轉送至: {doc_url}")
        return doc_url

    except Exception as e:
        print(f"❌ 建立 Google Doc 失敗: {e}")
        return None
    

def get_doc_text_content(document_id: str):
    """
    輸入 document_id，Return 該 Doc 內的完整純文字內容
    """
    # 這裡使用你之前定義好的 get_google_services()
    docs_service, _ = get_google_services() 

    try:
        doc = docs_service.documents().get(documentId=document_id).execute()
        doc_content = doc.get('body').get('content')
        
        full_text = ""
        for element in doc_content:
            if 'paragraph' in element:
                elements = element.get('paragraph').get('elements')
                for text_run in elements:
                    if 'textRun' in text_run:
                        full_text += text_run.get('textRun').get('content')
        
        print(f"成功擷取 Doc 內容，長度: {len(full_text)}")
        return full_text
    except Exception as e:
        print(f"擷取 Google Doc 內容失敗: {e}")
        return None

# --- 使用範例 ---
# title = "利物浦歐聯大勝"
# content = "這是新聞的詳細內容..."
# img_url = "https://example.com/news_image.jpg" # 必須是直接指向圖片的公開連結
# create_news_doc(title, content, img_url)

if __name__ == "__main__":
    title = "利物浦歐聯"
    content = "這是新聞的詳細內容..."
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/640px-Camponotus_flavomarginatus_ant.jpg"
    create_news_doc(title, content, image_url)