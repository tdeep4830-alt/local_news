import svgwrite
import io
from PIL import ImageFont, ImageDraw, Image, ImageOps
import os
import requests
import time
import sys
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# 針對 macOS Homebrew 路徑嘅修正
if sys.platform == 'darwin':
    # 檢查 /opt/homebrew/lib 係咪已經喺搜尋路徑入面
    homebrew_lib = '/opt/homebrew/lib'
    if os.path.exists(homebrew_lib):
        if 'DYLD_LIBRARY_PATH' in os.environ:
            os.environ['DYLD_LIBRARY_PATH'] = f"{homebrew_lib}:{os.environ['DYLD_LIBRARY_PATH']}"
        else:
            os.environ['DYLD_LIBRARY_PATH'] = homebrew_lib

def get_image_pixel_size(image_path: str):
    """
    獲取圖片的像素尺寸 (Width, Height)
    """
    try:
        if not os.path.exists(image_path):
            print(f"❌ 錯誤：找不到檔案 {image_path}")
            return None

        with Image.open(image_path) as img:
            width, height = img.size
            print(f"📷 圖片尺寸: {width}px x {height}px")
            return {"width": width, "height": height}
            
    except Exception as e:
        print(f"❌ 無法讀取圖片尺寸: {e}")
        return None

def calculate_autofit_font_size(text, max_w, max_h, font_path, start_size=70):
    """
    Observability 工具：計算最適合畫布大小的字體像素 (in px)
    確保文字寬度在 max_w 的 90% 以內。
    """
    try:
        current_size = start_size
        
        # 開啟字型，如果檔案不存在，會跳到 except 
        # 你可以指定你想用的繁體字型檔路徑 (例如: "PingFang.ttc")
        # 如果不知道路徑，可以放一張 "default.ttf" 在同一資料夾
        font = ImageFont.truetype(font_path, current_size)
        
        # Observability 檢查：確保字型支援中文
        if not font.getname()[0]:
             print(f"警告：{font_path} 可能不支援中文渲染")
        
        # 迴圈計算：直到寬度符合要求或字體大小小於 10
        # Pillow v10 之後用 getbbox() 代替 getsize()
        while current_size > 10:
            font = ImageFont.truetype(font_path, current_size)
            # (left, top, right, bottom)
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # 檢查是否超出畫布 90% 寬度
            if text_width <= max_w * 0.9 and text_height <= max_h * 0.9:
                # 符合要求，跳出迴圈
                break
            # 如果太寬，將字體大小減 1
            current_size -= 1

        print(f"📊 動態計算字體大小: {current_size}px (文字寬度: {text_width}px, 畫布寬度: {max_w}px)")
        return current_size

    except Exception as e:
        print(f"⚠️ 無法計算字體大小 (可能是找不到字型檔)，回傳預設 30px: {e}")
        # 回傳一個保守的後備字體大小
        return 30



def download_jpg(url: str, title: int):
    """
    從指定 URL 下載 JPG 並以自定義名稱儲存
    """
    # 1. 確保儲存資料夾存在
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    photo_name = re.sub(r'[\\/*?:"<>|\s]+', "_", str(title))  # 移除不合法字元

    # 2. 處理副檔名：確保檔名以 .jpg 結尾
    if not photo_name.lower().endswith(".jpg"):
        photo_name += ".jpg"

    file_path = os.path.join("downloads", photo_name)

    try:
        # 3. 發送請求，加入 Timeout 避免程式卡死
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()

        # 4. Observability 檢查：驗證是否為圖片格式
        content_type = response.headers.get('Content-Type', '')
        if 'image' not in content_type:
            print(f"警告：URL 內容可能不是圖片 (Content-Type: {content_type})")

        # 5. 分段寫入檔案，節省記憶體 (適合處理大圖)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"[{time.strftime('%H:%M:%S')}] 圖片已成功儲存至: {file_path}")
        return file_path

    except requests.exceptions.RequestException as e:
        print(f"下載失敗 ({url}): {e}")
        return None


def split_text_by_punctuation(text):
    """
    根據標點符號拆分文字。
    正則表達式 [，。！？,!?;] 可以根據需求增加更多標點。
    """
    # 使用 re.split 拆分，並過濾掉拆分後可能產生的空字串
    parts = re.split(r'[，。！？,!?;]', text)
    
    lines = []
    current_line = ""
    
    # 這裡的邏輯是將標點符號保留在該行末尾
    for i in range(0, len(parts)-1, 2):
        lines.append(parts[i] + parts[i+1])
    
    # 處理最後一段沒有標點的情況
    if len(parts) % 2 != 0 and parts[-1]:
        lines.append(parts[-1])
        
    return "\n".join(lines)

def split_text_custom(text):
    """
    根據標點符號及「空格」拆分文字並移除它們。
    這能讓多行文字更均勻，從而增大字體。
    """
    # 加入 \s 來捕捉空格
    parts = re.split(r'[，。！？,!?; \s]', text)
    
    # 過濾空字串並用換行符號結合
    lines = [p.strip() for p in parts if p.strip()]
    return "\n".join(lines)

def add_text_to_image_with_background(input_path, text, title, breaking=0, source=""):
    try:
        # 1. 處理文字換行 (整合標點與空格移除)
        processed_text = split_text_custom(text)
        logging.info(f"原始文字: {text} -> 處理後文字: \n{processed_text}")

        # 2. 定義畫布大小
        BG_W, BG_H = 1080, 1350
        
        # 3. 處理底圖
        img_bg = Image.open(input_path).convert("RGBA")
        img_bg = ImageOps.fit(img_bg, (BG_W, BG_H), method=Image.Resampling.LANCZOS)
        
        # 4. 建立 Overlay 疊加層
        overlay = Image.new("RGBA", (BG_W, BG_H), (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        
        lower_third_h = int(BG_H * 0.35)
        lower_third_y = BG_H - lower_third_h
        
        # 畫半透明底色
        draw_overlay.rectangle([(0, lower_third_y), (BG_W, BG_H)], fill=(0, 0, 0, 190))
        
        # 畫 Highlight 頂線
        line_color = (255, 204, 0, 255) # 預設黃色
        if breaking == 1:
            line_color = (255, 50, 50, 255) # Breaking 時改用紅色更有張力
            
        draw_overlay.rectangle([(0, lower_third_y), (BG_W, lower_third_y + 10)], fill=line_color)

        # --- 新增功能：Breaking 標籤 ---
        font_path = "/Users/tobychunyu/Desktop/Deep/local_news/public/GenSenRounded2TC-M.otf"
        if breaking == 1:
            # 畫一個紅色方塊在黃線上方
            tag_w, tag_h = 280, 70
            tag_x, tag_y = 40, lower_third_y - tag_h
            draw_overlay.rectangle([(tag_x, tag_y), (tag_x + tag_w, tag_y + tag_h)], fill=(255, 0, 0, 255))
            
            # 寫上 "BREAKING" 字眼
            breaking_font = ImageFont.truetype(font_path, 40)
            draw_overlay.text((tag_x + 25, tag_y + 10), "BREAKING", fill=(255, 255, 255, 255), font=breaking_font)

        # 將疊加層合併
        final_img = Image.alpha_composite(img_bg, overlay)
        draw = ImageDraw.Draw(final_img)
        
        # 5. 計算文字區域 (標題)
        text_area_w = int(BG_W * 0.95)
        margin_y = 50
        text_area_y_start = lower_third_y + margin_y + 10
        text_area_h = lower_third_h - (margin_y * 2) - 10
        
        lines = processed_text.split('\n')
        longest_line = max(lines, key=len)
        
        final_font_size_px = calculate_autofit_font_size(
            longest_line, 
            text_area_w, 
            text_area_h / 2.2, 
            font_path, 
            start_size=150
        )
        font = ImageFont.truetype(font_path, final_font_size_px)

        # 繪製標題文字
        bbox = draw.multiline_textbbox((0, 0), processed_text, font=font, spacing=20)
        text_h = bbox[3] - bbox[1]
        text_x = (BG_W - (bbox[2] - bbox[0])) // 2
        text_y = text_area_y_start + (text_area_h - text_h) // 2
        
        draw.multiline_text((text_x, text_y), processed_text, fill=(255, 255, 255, 255), 
                            font=font, spacing=20, align="center")

        # --- 新增功能：右下角 Source ---
        if source:
            source_text = f"Source: {source}"
            source_font = ImageFont.truetype(font_path, 24) # 較小的字體
            # 取得文字寬度以便靠右對齊
            s_bbox = draw.textbbox((0, 0), source_text, font=source_font)
            s_w = s_bbox[2] - s_bbox[0]
            # 放在右下角，留 20px 邊距
            draw.text((BG_W - s_w - 20, BG_H - 40), source_text, fill=(200, 200, 200, 180), font=source_font)

        # 7. 儲存
        final_img = final_img.convert("RGB")
        output_path = f"/Users/tobychunyu/Desktop/Deep/local_news/downloads/{title}_with_title.jpg"
        final_img.save(output_path, quality=95) 
        logging.info(f"✅ 圖片已成功儲存至: {output_path} (Breaking: {breaking})")

    except Exception as e:
        logging.error(f"❌ 處理圖片時出錯: {e}")
        raise

# --- 測試執行 ---
if __name__ == "__main__":
    add_text_to_image_with_background(
        input_path="/Users/tobychunyu/Desktop/Deep/local_news/downloads/BBC_Antiques_Roadshow_values_'outrageous'_fashions_at_a_small_fortune.jpg",
        text="Liverpool Echo 最新新聞，這是一段測試標題，用來驗證圖片生成腳本嘅功能同效果。",
        title="header",
        source="Liverpool Echo",
        breaking=1
    )
