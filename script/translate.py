from openai import OpenAI
import json
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

def translate_news_with_deepseek(title: str, content: str) -> dict:
    """
    使用 DeepSeek Reasoner API 將新聞翻譯為香港中文
    """
    # 在函數內初始化 client，避免 import 時因 key 未設定而 crash
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com/v1"
    )

    prompt = f"""
    請將以下新聞標題及內文翻譯成「香港中文」(Traditional Chinese - Hong Kong)，並縮短新聞標題至15個字以內。
    要求：
    1. 使用香港常用的詞彙及語法（例如：'Football' 譯作 '足球', 'Update' 譯作 '更新'）。
    2. 確保翻譯自然且風格為香港中文的書面語。
    3. 若專有名詞及人名無法翻譯，請保留原文。
    4. 必須以 JSON 格式回傳，格式如下：
       {{
         "translated_title": "標題內容",
         "shortened_title": "縮短後標題",
         "translated_content": "內文內容"
       }}

    原文標題：{title}
    原文內文：{content}
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": "你是一位專業的新聞翻譯官，擅長將英文新聞翻譯成香港中文的書面語。"},
                {"role": "user", "content": prompt},
            ],
        )

        result_text = response.choices[0].message.content

        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        return json.loads(result_text)

    except Exception as e:
        print(f"DeepSeek 翻譯失敗: {e}")
        return {"translated_title": "翻譯失敗", "translated_content": ""}


# --- 測試用法 ---
if __name__ == "__main__":
    news_json = translate_news_with_deepseek("Test title", "Test content")
    print(news_json)
