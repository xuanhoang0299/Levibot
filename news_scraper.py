import logging
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from datetime import datetime, timedelta
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

# CẦN ĐIỀN THÔNG TIN TỪ my.telegram.org
API_ID = int(os.getenv("TELEGRAM_API_ID", "35049369"))  # Thay bằng API_ID thật (số nguyên)
API_HASH = os.getenv("TELEGRAM_API_HASH", "YOUR_API_HASH")  # Thay bằng API_HASH thật (chuỗi)
import os
# Tên file session cục bộ để lưu đăng nhập
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_NAME = os.path.join(BASE_DIR, "my_news_scraper")

# CẦN ĐIỀN THÔNG TIN TỪ aistudio.google.com
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_2", "YOUR_GEMINI_KEY")

# Kênh muốn đọc tin
TARGET_CHANNEL = "ThuanCapital" # Ví dụ: "tintuccrypto"

logger = logging.getLogger(__name__)

# Cấu hình Gemini AI
client_ai = genai.Client(api_key=GEMINI_API_KEY)

async def fetch_messages_from_channel(channel_username, limit=50):
    """
    Dùng Telethon để đóng vai tài khoản của bạn đi đọc tin.
    Sẽ yêu cầu nhập SĐT và OTP lần đầu chạy.
    """
    logger.info(f"Bắt đầu đọc tin từ kênh {channel_username}...")
    
    # Khởi tạo Client
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.connect()
    
    # Nếu chưa đăng nhập, Telethon sẽ tự văng lỗi ở trong hàm MarketBot chạy nền.
    # Do đó, LẦN ĐẦU TIÊN phải chạy file script này trực tiếp trên Terminal để nhập mã OTP!
    if not await client.is_user_authorized():
        logger.error("CHƯA ĐĂNG NHẬP TELETHON! Vui lòng chạy file news_scraper.py trực tiếp để đăng nhập lần đầu.")
        await client.disconnect()
        return []
    
    try:
        # Lấy entity của Channel
        entity = await client.get_entity(channel_username)
        
        # Chỉ lấy tin nhắn trong vòng 24h qua
        recent_messages = []
        yesterday = datetime.now() - timedelta(hours=24)
        
        async for message in client.iter_messages(entity, limit=limit):
            # message.date là timezone-aware (thường là UTC)
            if message.date and message.date.replace(tzinfo=None) > yesterday:
                if message.text:  # Chỉ lấy tin nhắn chữ
                    msg_link = f"https://t.me/{channel_username}/{message.id}"
                    msg_date = message.date.strftime("%d/%m %H:%M")
                    formatted_msg = f"RAW_TEXT: {message.text}\nTIME: {msg_date}\nLINK: {msg_link}"
                    recent_messages.append(formatted_msg)
                    
        await client.disconnect()
        return recent_messages
        
    except Exception as e:
        logger.error(f"Lỗi khi đọc tin từ {channel_username}: {e}")
        await client.disconnect()
        return []

def summarize_with_gemini(messages_list):
    """
    Gửi danh sách tin nhắn cho Gemini và yêu cầu tóm tắt.
    """
    if not messages_list:
        return "📉 Không có tin tức mới nào trong 24h qua trên kênh này."
        
    logger.info(f"Đang gửi {len(messages_list)} tin nhắn cho Gemini tóm tắt...")
    
    # Gộp tất cả tin nhắn thành 1 đoạn văn bản dài
    raw_text = "\n\n--- TIN TỨC ---\n\n".join(messages_list)
    
    prompt = f"""
    Dưới đây là danh sách các tin tức trong 24h qua được thu thập từ kênh Telegram. Mỗi tin tức sẽ có Nội dung (RAW_TEXT), Thời gian (TIME), và Đường dẫn (LINK).
    Nhiệm vụ của bạn là:
    1. Đọc và chọn lọc, loại bỏ hoàn toàn các tin rác, quảng cáo hoặc tin không quan trọng.
    2. Giữ lại những tin tức đáng chú ý và viết lại chúng thành một Tiêu đề/Đoạn tóm tắt thật súc tích, dễ hiểu (khoảng 1-2 câu).
    3. Trình bày từng tin tức theo ĐÚNG định dạng sau (sử dụng icon số thứ tự 1️⃣, 2️⃣, 3️⃣... thay vì 1), 2), 3)... cho từng tin, In nghiêng đoạn thời gian và KHÔNG in nghiêng chữ ThuanCapital hay chữ LINK, bắt buộc ẩn đường dẫn dưới chữ "LINK"):
    
    1️⃣ [Tiêu đề tóm tắt nội dung tin tức]
    _[Thời gian TIME]_ via ThuanCapital 🚀 [LINK](Đường_dẫn_LINK)

    (Mỗi phần tin tức cách nhau 1 dòng trống).
    
    LƯU Ý RẤT QUAN TRỌNG: 
    - Bạn CHỈ ĐƯỢC chọn lọc ra TỐI ĐA 8 đến 10 tin tức quan trọng đáng chú ý nhất. TUYỆT ĐỐI không viết quá dài để tránh vượt quá giới hạn hiển thị.
    - TUYỆT ĐỐI KHÔNG sử dụng ký tự gạch chéo ngược "\\" để escape các dấu ngoặc vuông `[]` và ngoặc đơn `()` của đường link. Phải xuất chuẩn xác cú pháp Markdown `[LINK](url)`.

    Nội dung danh sách tin tức gốc:
    {raw_text}
    """
    
    try:
        response = client_ai.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"Lỗi khi gọi Gemini: {e}")
        return "❌ Lỗi khi AI tóm tắt tin tức. Vui lòng kiểm tra lại cấu hình."

async def get_daily_summary():
    """Hàm chính gọi từ market_bot.py"""
    if API_ID == 1234567 or GEMINI_API_KEY.startswith("your_"):
        return "❌ BẠN CHƯA CẤU HÌNH API TRONG `news_scraper.py`! Hãy mở file lên điền API_ID, API_HASH và GEMINI_KEY."
        
    messages = await fetch_messages_from_channel(TARGET_CHANNEL, limit=30)
    summary = summarize_with_gemini(messages)
    
    final_message = f"📰 *BẢN TIN SÁNG ({TARGET_CHANNEL})*\n\n{summary}"
    
    # Telegram giới hạn 4096 ký tự mỗi tin nhắn, cắt bớt nếu quá dài
    if len(final_message) > 4000:
        final_message = final_message[:4000] + "\n...(Tin tức đã bị cắt bớt do quá dài)"
    
    return final_message

async def init_session():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("Đang khởi động chế độ đăng nhập lần đầu...")
    # Telethon sẽ tự tương tác với Terminal để xin SĐT và OTP
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()
    print("\n✅ ĐĂNG NHẬP THÀNH CÔNG! File session.name đã được tạo.")
    print("Từ giờ market_bot.py đã có thể tĩnh lặng chạy ngầm đi đọc báo.")
    await client.disconnect()

# Khối này dùng để thiết lập đăng nhập lần đầu tiên!
if __name__ == "__main__":
    if API_ID == 1234567:
        print("XIN HÃY MỞ FILE LÊN VÀ CHỈNH SỬA CÁC BIẾN API Ở TRÊN TRƯỚC TIÊN!")
    else:
        asyncio.run(init_session())
