from flask import Flask, request, jsonify
import json
from script.append_to_google_doc import get_doc_text_content
# 匯入你之前寫好的 Google Doc 同 Telegram Function
# from photo_producer import get_doc_text_content, send_to_telegram 

app = Flask(__name__)

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    data = request.json
    
    # 檢查係咪 Callback Query (即係撳掣動作)
    if 'callback_query' in data:
        callback_data = data['callback_query']['data']
        chat_id = data['callback_query']['message']['chat']['id']
        
        if callback_data.startswith('approve_'):
            doc_id = callback_data.replace('approve_', '')
            print(f"🚀 收到 Approve 請求！Document ID: {doc_id}")
            
            # 1. 喺 Google Doc 攞返文字
            content = get_doc_text_content(doc_id)
            
            # 2. 之後準備出 Post (Placeholder)
            # post_to_social_media(content)
            
            # 3. 回覆 Telegram 話俾你聽處理緊
            return jsonify({"status": "success", "message": "Approving..."})

    return jsonify({"status": "ignored"}), 200

if __name__ == '__main__':
    # 喺本地 5000 Port 行
    app.run(port=5000)