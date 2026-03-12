from openai import OpenAI
import json
from dotenv import load_dotenv
import os

load_dotenv()

# 設定你的 DeepSeek API Key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 初始化 Client (DeepSeek API 兼容 OpenAI 格式)
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

def translate_news_with_deepseek(title: str, content: str) -> dict:
    """
    使用 DeepSeek Reasoner API 將新聞翻譯為香港中文
    """
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
        # 使用 deepseek-reasoner 模型 (具備思考推理能力)
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": "你是一位專業的新聞翻譯官，擅長將英文新聞翻譯成香港中文的書面語。"},
                {"role": "user", "content": prompt},
            ],
            # Reasoner 模型通常建議不設定 response_format={"type": "json_object"} 
            # 而是直接在 Prompt 裡面要求，因為它會先輸出思考過程 (Reasoning)
        )

        # 獲取模型回傳的文字內容
        result_text = response.choices[0].message.content
        
        # 由於 Reasoner 可能會包含 Markdown 標籤，我們需要清理一下
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        return json.loads(result_text)

    except Exception as e:
        print(f"DeepSeek 翻譯失敗: {e}")
        return {"translated_title": "翻譯失敗", "translated_content": ""}

# --- 測試用法 ---
news_json = translate_news_with_deepseek("Full list of countries on Foreign Office 'do not travel' list","With tensions rising in the Middle East, the Foreign, Commonwealth & Development Office (FCDO) has been updating its foreign travel advice for many countries. If you are travelling anywhere in the Middle East,you should monitor the latest travel advice, read guidance on being affected by the crisis abroad and follow advice from local authorities.\nSince tensions escalated over the weekend, 20 countries have seen FCDO updates.Conflict has escalatedafter the US and Israel launched a wave of strikes, killing Iran's Supreme Leader Ali Khamenei. Blasts were reported in Jerusalem in Israel, Dubai and Abu Dhabi in the UAE, Doha in Qatar and Manama in Bahrain on the third day of the conflict.\nSir Keir Starmer defended his decisionnot to allow UK bases to be used by the US in the initial strikes against Iran in the face of criticism from Donald Trump.\nThe Prime Minister granted permission on Sunday for the US to use British bases to target Iran’s missile launchers and stores to help protect countries targeted by Tehran.\nAround 300,000 Britons are believed to be in countries targeted by Iran, with 102,000 registering their presence with the Foreign Office as officials worked on contingency plansincluding a possible mass evacuation. Sir Keir said the government is \"looking at all options to support our people\".\nWe have rounded up the full list of countries with updated travel warnings from the Foreign Office.\nPolitical conflicts, natural disasters and safety concerns are among the reasons the UK Foreign Office will recommend British nationals to steer clear of certain destinations.\nOf 226 countries or territories with foreign travel advice pages, 76 are currently flagged as having no-go zones due to security issues, health risks and legal differences with the UK.\nIf you choose to make the journey against FCDO advice,travel insurance may be invalidated, and there may be a lack of consular support in the event of an emergency overseas.\nAirlines worldwide havecontinued to ground flightsthroughout the Middle East following \"major combat operations\" launched by the US and Israel across Iran.\nNumerous British holidaymakers who favourdestinations such as Dubaihave experienced disruption to their travel arrangements. You should stay updated with the latest advice from the airline you are travelling with.\nEnsure our latest news and what's on headlines always appear at the top of your Google search by making us a preferred source.Click here to activateor add us as a preferred source in your Google search settings.")
print(news_json['shortened_title'])