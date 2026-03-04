import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import time
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Thay thế bằng Token của bot từ BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
# Thay thế bằng Chat ID của bạn (gõ /start với bot để lấy Chat ID)
CHAT_ID = os.getenv("CHAT_ID", "YOUR_CHAT_ID")

# Bật log để xem lỗi nếu có
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_crypto_summary() -> str:
    """Hàm lấy giá Crypto từ CoinGecko API"""
    URL = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,solana,binancecoin,ripple",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    
    try:
        response = requests.get(URL, params=params, timeout=10)
        data = response.json()
        
        symbols = {
            "bitcoin": "₿ Bitcoin (BTC)",
            "ethereum": "♦ Ethereum (ETH)",
            "solana": "◎ Solana (SOL)",
            "binancecoin": "🟡 BNB (BNB)",
            "ripple": "✖ XRP (XRP)"
        }
        
        message = "📊 *BẢN TIN CRYPTO HÀNG NGÀY*\n\n"
        for coin_id, info in symbols.items():
            if coin_id in data:
                price = data[coin_id].get("usd", 0)
                change = data[coin_id].get("usd_24h_change", 0)
                trend = "📈" if change >= 0 else "📉"
                message += f"{info}:\n"
                message += f"💵 Giá: ${price:,.2f}\n"
                message += f"{trend} 24h: {change:+.2f}%\n\n"
                
        message += "⚡ _Dữ liệu giá: CoinGecko_\n\n"
        
        # Thêm phần tin tức
        news = get_crypto_news()
        if news:
            message += news
            message += "\n🗞 _Nguồn tin: CryptoCompare_"
            
        return message
        
    except Exception as e:
        logger.error(f"Lỗi khi lấy dữ liệu crypto: {e}")
        return "❌ Lỗi khi lấy dữ liệu crypto. Vui lòng thử lại sau."

def get_crypto_news() -> str:
    """Hàm lấy tin tức Crypto mới nhất từ CryptoCompare"""
    URL = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
    try:
        response = requests.get(URL, timeout=10)
        data = response.json()
        
        if data.get("Type") == 100:
            news_list = data.get("Data", [])[:3] # Lấy 3 tin mới nhất
            if not news_list:
                 return ""
                 
            news_text = "📰 *TIN TỨC NỔI BẬT (Tiếng Anh)*\n"
            for item in news_list:
                title = item.get("title", "No Title")
                url = item.get("url", "")
                
                # Rút gọn tiêu đề nếu quá dài để tránh tin nhắn bị rối
                if len(title) > 65:
                     title = title[:62] + "..."
                     
                news_text += f"▪️ [{title}]({url})\n"
                
            return news_text
        return ""
    except Exception as e:
        logger.error(f"Lỗi khi lấy tin tức: {e}")
        return ""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lệnh /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    await update.message.reply_html(
        rf"Chào {user.mention_html()}! Mình là bot tổng hợp giá Crypto. 🤖"
        rf"\n\nĐể mình có thể gửi tin tự động mỗi ngày cho bạn, hãy copy dán mã Chat ID này vào biến <code>CHAT_ID</code> trong file code nhé:"
        rf"\n\n👉 Chat ID của bạn: <code>{chat_id}</code>"
        rf"\n\nGõ lệnh /crypto để xem giá ngay lập tức!"
    )

async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gửi bản tin khi user gõ thủ công /crypto"""
    summary = get_crypto_summary()
    await update.message.reply_text(summary, parse_mode='Markdown')

async def send_daily_summary(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tự động gửi bản tin hàng ngày"""
    if str(CHAT_ID).startswith("YOUR"):
        logger.warning("Chưa cấu hình CHAT_ID. Bot không thể gửi tin tự động.")
        return
        
    summary = get_crypto_summary()
    try:
        await context.bot.send_message(chat_id=CHAT_ID, text=summary, parse_mode='Markdown')
        logger.info(f"Đã gửi bản tin hàng ngày tới chat {CHAT_ID}")
    except Exception as e:
        logger.error(f"Lỗi khi gửi bản tin tự động: {e}")

def main() -> None:
    """Hàm khởi chạy bot"""
    if BOT_TOKEN.startswith("YOUR"):
        print("❌ LỖI: Vui lòng điền BOT_TOKEN của bạn vào file code trước khi chạy (dòng 9)!")
        print("Bạn có thể lấy Token bằng cách chat với @BotFather trên Telegram.")
        return

    # Khởi tạo Application
    app = Application.builder().token(BOT_TOKEN).build()

    # Đăng ký các lệnh
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("crypto", crypto_command))

    # Cài đặt lịch gửi tự động hàng ngày (0:30 AM UTC = 7:30 AM Giờ Việt Nam)
    t = time(hour=0, minute=30, second=0) 
    
    # Lên lịch tác vụ
    job_queue = app.job_queue
    job_queue.run_daily(send_daily_summary, t)

    print("✅ Bot đang chạy! Nhấn Ctrl-C để dừng.")
    # Bắt đầu nghe tin nhắn
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
