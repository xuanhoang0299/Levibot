import os
import sys
import asyncio
from telethon import TelegramClient, events
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Ép Windows Terminal hỗ trợ in ra các emoji 
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ================= CẤU HÌNH API ================= #
# 1. Thay thông tin Telegram của bạn vào đây
API_ID = int(os.getenv("TELEGRAM_API_ID", "35049369"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "YOUR_API_HASH")

# 2. Thay Gemini API Key vào đây API KEY NÀY LÀ CỦA XUANHOANG0299
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_1", "YOUR_GEMINI_KEY")

# ================ THÔNG TIN NHÓM ================ #
TARGET_GROUP = 'TradingMentor_Crypto'  # Username hoặc link rút gọn của group

# Danh sách các lệnh và người dùng cần tóm tắt tương ứng (bỏ dấu @)
USER_COMMANDS = {
    '/tomtatsan': 'LuuSanSan',
    '/tomtatbob': 'b0bby0ne',  # Thay username người thứ 2 vào đây
    '/tomtatvinh': 'trongvinhFA25',  # Thay username người thứ 3 vào đây
}
LIMIT_MESSAGES = 15                  # Số lượng tin nhắn gần nhất muốn lấy (tùy chỉnh)

# Cấu hình Gemini AI (Dùng bản flash nhanh, nhẹ, miễn phí và rất tốt cho văn bản)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Khởi tạo Client ngang mức global để các hàm dễ dùng chung
client = TelegramClient('my_account_session', API_ID, API_HASH)

async def get_summary(target_user):
    print(f"🔍 Đang tìm kiếm tin nhắn của @{target_user} trong group {TARGET_GROUP}...")
    messages_content = []
    
    # Lấy lịch sử tin nhắn của group, lọc theo user
    async for message in client.iter_messages(TARGET_GROUP, from_user=target_user, limit=LIMIT_MESSAGES):
        if message.text: # Chỉ lấy tin nhắn chữ
            date_str = message.date.strftime("%d/%m/%Y %H:%M")
            messages_content.append(f"[{date_str}] {message.text}")
    
    if not messages_content:
        return "❌ Không tìm thấy tin nhắn nào của người dùng này!"

    # Gộp các tin nhắn lại
    messages_content.reverse()
    full_text = "\n\n".join(messages_content)
    
    print(f"📥 Đã gom được {len(messages_content)} tin nhắn. Đang gửi cho Gemini để tóm tắt...")
    
    prompt = f"""
    Bạn là một trợ lý tài chính Crypto thông minh. Dưới đây là các tin nhắn của tài khoản @{target_user} trong một group Crypto.
    
    Lịch sử tin nhắn:
    {full_text}
    
    YÊU CẦU:
    1. Hãy tóm tắt lại các điểm chính mà người này chia sẻ.
    2. Chắt lọc ra các kèo giao dịch (nếu có: đồng coin nào, giá mua/bán, điểm cắt lỗ, kỳ vọng).
    3. Trích xuất nhận định thị trường chung của người này.
    4. Trình bày bằng Tiếng Việt, sử dụng định dạng rõ ràng (gạch đầu dòng, in đậm các giá trị quan trọng). Nếu không có kèo nào, hãy bỏ qua phần đó.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Lỗi khi tải mô hình Gemini: {e}"

# Bắt sự kiện: khi bạn gõ lệnh vào mục Saved Messages (me)
@client.on(events.NewMessage(chats='me'))
async def my_event_handler(event):
    if not event.raw_text:
        return
        
    text = event.raw_text.lower()
    
    # Tìm xem lệnh gõ vào có khớp với lệnh nào trong cấu hình không
    target_user = None
    for cmd, user in USER_COMMANDS.items():
        if text.startswith(cmd):
            target_user = user
            break
            
    if target_user:
        # Phản hồi lại ngay lập tức để bạn biết bot đã nhận lệnh
        await event.reply(f"⏳ Đang đi gom tin nhắn và tóm tắt cho @{target_user}, vui lòng chờ chút nhé...")
        
        # Chạy hàm thu thập và tóm tắt
        summary = await get_summary(target_user)
        
        print(f"✅ Đã lấy tóm tắt xong cho @{target_user}, đang gửi tin nhắn vào Telegram...")
        # Chia nhỏ tin nhắn nếu dài quá 4000 ký tự (giới hạn của Telegram)
        for i in range(0, len(summary), 4000):
            await event.reply(summary[i:i+4000])

async def main():
    await client.start()
    print("✅ Đã đăng nhập Telegram thành công!")
    print("🤖 Bot đang chạy ngầm và lắng nghe lệnh...")
    print("👉 HÃY VÀO MỤC 'Saved Messages' TRÊN TELEGRAM CỦA BẠN VÀ THỬ CÁC LỆNH SAU:")
    for cmd, user in USER_COMMANDS.items():
        print(f"   {cmd} -> Tóm tắt cho @{user}")
    
    # Duy trì bot chạy liên tục thay vì thoát ngay
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
