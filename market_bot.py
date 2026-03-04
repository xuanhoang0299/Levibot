import logging
import requests
import asyncio
from telegram import Update, LinkPreviewOptions
from telegram.ext import Application, CommandHandler, ContextTypes
import yfinance as yf
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime, time
import urllib3
import news_scraper
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Thay thế bằng Token của bot từ BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
# Thay thế bằng Chat ID của bạn (gõ /start với bot để lấy Chat ID)
CHAT_ID = os.getenv("CHAT_ID", "YOUR_CHAT_ID")

# ================= CẤU HÌNH API TELETHON & GEMINI ================= #
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "35049369"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "YOUR_API_HASH")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_1", "YOUR_GEMINI_KEY")

TARGET_GROUP = 'TradingMentor_Crypto'  

# Danh sách các lệnh và người dùng cần tóm tắt tương ứng (bỏ dấu @)
USER_COMMANDS = {
    'tomtatsan': 'LuuSanSan',
    'tomtatbob': 'b0bby0ne',
    'tomtatvinh': 'trongvinhFA25',
}
LIMIT_MESSAGES = 15                   

import google.generativeai as genai
genai.configure(api_key=GEMINI_API_KEY)
summary_model = genai.GenerativeModel('gemini-2.5-flash')

# Khởi tạo Telethon Client (dùng để đọc tin nhắn Group như một user)
telethon_client = TelegramClient('my_account_session', TELEGRAM_API_ID, TELEGRAM_API_HASH)


logger = logging.getLogger(__name__)

def fetch_sjc_gold(market_data):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get("https://sjc.com.vn/xml/tygiavang.xml", headers=headers, timeout=10, verify=False)
        content = resp.text
        match_buy = re.search(r'buy="([^"]+)"', content)
        match_sell = re.search(r'sell="([^"]+)"', content)
        if match_buy and match_sell:
            market_data["gold_buy"] = match_buy.group(1)
            market_data["gold_sell"] = match_sell.group(1)
            return True
    except Exception as e:
        logger.error(f"Lỗi Gold SJC: {e}")
    return False

def fetch_btmh_gold(market_data):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get("https://baotinmanhhai.vn/", headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        row = soup.find(string=re.compile('Vàng miếng SJC', re.I))
        if row and row.parent and row.parent.parent:
            text_row = row.parent.parent.get_text(separator='|', strip=True)
            parts = text_row.split('|')
            prices = [p for p in parts if p.replace('.', '').isdigit()]
            if len(prices) >= 2:
                market_data["gold_buy"] = prices[0].replace('.', '')
                market_data["gold_sell"] = prices[1].replace('.', '')
                return True
    except Exception as e:
        logger.error(f"Lỗi Gold BTMH: {e}")
    return False

def fetch_gold(market_data):
    if not fetch_sjc_gold(market_data):
        fetch_btmh_gold(market_data)

def fetch_world_gold(market_data):
    try:
        ticker = yf.Ticker("GC=F")
        price = ticker.info.get('regularMarketPrice')
        if not price:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
        if price:
            market_data["world_gold"] = f"{price:,.1f}"
    except Exception as e:
        logger.error(f"Lỗi World Gold: {e}")

def fetch_oil(market_data):
    try:
        ticker = yf.Ticker("CL=F")
        price = ticker.info.get('regularMarketPrice')
        if not price:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
        if price:
            market_data["oil"] = f"{price:.2f}"
    except Exception as e:
        logger.error(f"Lỗi Oil WTI: {e}")

def fetch_usdt_p2p(market_data):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "content-type": "application/json"
    }
    # Lọc giá dựa trên số tiền VND (VD: 10,000,000 VND)
    fiat_amount = "10000000"
    
    data_buy = {
        "page": 1, "rows": 1, "payTypes": [], "asset": "USDT",
        "tradeType": "BUY", "fiat": "VND", "publisherType": "merchant",
        "transAmount": fiat_amount
    }
    data_sell = {
        "page": 1, "rows": 1, "payTypes": [], "asset": "USDT",
        "tradeType": "SELL", "fiat": "VND", "publisherType": "merchant",
        "transAmount": fiat_amount
    }
    try:
        r_buy = requests.post('https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search', headers=headers, json=data_buy, timeout=10)
        buy_price = r_buy.json()['data'][0]['adv']['price']
        
        r_sell = requests.post('https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search', headers=headers, json=data_sell, timeout=10)
        sell_price = r_sell.json()['data'][0]['adv']['price']
        
        market_data["usd_buy"] = buy_price
        market_data["usd_sell"] = sell_price
    except Exception as e:
        logger.error(f"Lỗi USDT Binance: {e}")

def fetch_btc(market_data):
    try:
        ticker = yf.Ticker("BTC-USD")
        price = ticker.info.get('regularMarketPrice')
        if not price:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
        if price:
            market_data["btc"] = f"{price:,.0f}"
    except Exception as e:
        logger.error(f"Lỗi BTC: {e}")

def fetch_vni(market_data):
    try:
        url = "https://vn.investing.com/indices/vn"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        price_el = soup.find(attrs={"data-test": "instrument-price-last"})
        if price_el:
            price = price_el.get_text(strip=True)
            market_data["vni"] = price
    except Exception as e:
        logger.error(f"Lỗi VNI: {e}")

def get_market_data():
    market_data = {
        "gold_buy": "0", "gold_sell": "0",
        "world_gold": "0.0",
        "oil": "0.0",
        "usd_buy": "0", "usd_sell": "0",
        "btc": "0",
        "vni": "0"
    }
    fetch_gold(market_data)
    fetch_world_gold(market_data)
    fetch_oil(market_data)
    fetch_usdt_p2p(market_data)
    fetch_btc(market_data)
    fetch_vni(market_data)
    return market_data

async def wl_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    waiting_msg = await update.message.reply_text("⏳ Đang lấy dữ liệu thị trường...")
    
    market_data = await asyncio.to_thread(get_market_data)
    
    t_gold_buy = market_data['gold_buy']
    t_gold_sell = market_data['gold_sell']
    if len(t_gold_buy) >= 7 and t_gold_buy.endswith('000'):
        t_gold_buy = t_gold_buy[:-3]
    if len(t_gold_sell) >= 7 and t_gold_sell.endswith('000'):
        t_gold_sell = t_gold_sell[:-3]

    now = datetime.now().strftime("%H:%M:%S")
    
    message = (
        f"📊 *THỊ TRƯỜNG HÔM NAY* ({now})\n\n"
        f"🪙 *BTC* : ${market_data['btc']}\n"
        f"💵 *USDT*: Mua {market_data['usd_buy']} - Bán {market_data['usd_sell']}\n"
        f"🥇 *SJC* : Mua {t_gold_buy} - Bán {t_gold_sell}\n"
        f"💰 *XAU* : ${market_data['world_gold']}\n"
        f"🛢 *OIL* : ${market_data['oil']}\n"
        f"📈 *VNI* : {market_data['vni']}"
    )
    
    await waiting_msg.edit_text(message, parse_mode='Markdown')

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    waiting_msg = await update.message.reply_text("⏳ Đang đi đọc báo và tóm tắt tin tức. Quá trình này có thể mất 15-30 giây...")
    try:
        # Gọi hàm get_daily_summary không dùng await vì trong đó có cả đồng bộ & bất đồng bộ nên dễ xung đột nếu không bọc
        # Tốt nhất là bọc asyncio.to_thread nếu trong đó có block
        # Tuy nhiên hàm trong news_scraper được viết bằng asycnio rồi
        summary = await news_scraper.get_daily_summary()
        await waiting_msg.edit_text(summary, parse_mode='Markdown', link_preview_options=LinkPreviewOptions(is_disabled=True))
    except Exception as e:
        logger.error(f"Lỗi khi lấy tin tức: {e}")
        await waiting_msg.edit_text(f"❌ Có lỗi xảy ra khi tóm tắt tin tức: {e}")

async def get_summary(target_user):
    if not telethon_client.is_connected():
        await telethon_client.connect()
        
    messages_content = []
    
    # Lấy lịch sử tin nhắn của group, lọc theo user
    async for message in telethon_client.iter_messages(TARGET_GROUP, from_user=target_user, limit=LIMIT_MESSAGES):
        if message.text: 
            date_str = message.date.strftime("%d/%m/%Y %H:%M")
            messages_content.append(f"[{date_str}] {message.text}")
    
    if not messages_content:
        return f"❌ Không tìm thấy tin nhắn nào của @{target_user}!"

    # Gộp các tin nhắn lại
    messages_content.reverse()
    full_text = "\n\n".join(messages_content)
    
    prompt = f"""
    Bạn là một trợ lý tài chính Crypto thông minh. Dưới đây là các tin nhắn của tài khoản @{target_user} trong một group Crypto.
    
    Lịch sử tin nhắn:
    {full_text}
    
    YÊU CẦU DÀNH CHO BẠN VỀ ĐỊNH DẠNG VÀ NỘI DUNG (TUYỆT ĐỐI TUÂN THỦ):
    - TUYỆT ĐỐI KHÔNG sử dụng dấu sao (*) hay (**) trong lập văn bản (gạch đầu dòng hoặc in đậm).
    - Dùng thẻ HTML <b>...</b> để in đậm.
    - Hai tiêu đề chính phải in HOA và in đậm như sau:
      <b>GÓC NHÌN & NHẬN ĐỊNH THỊ TRƯỜNG</b>
      <b>CÁC KÈO GIAO DỊCH</b>
    - Cứ mỗi ý lớn trình bày thì dùng biểu tượng chấm tròn ( • ) ở đầu dòng.
    - VỚI PHẦN NHẬN ĐỊNH: Tóm tắt đầy đủ, rõ ràng các phân tích dự đoán thành các câu trọn vẹn. Trong mỗi câu, chọn <b>in đậm 1-2 từ khóa</b> cốt lõi nhất để dễ đọc lướt.
    - VỚI PHẦN KÈO GIAO DỊCH, hãy thống nhất trình bày theo cấu trúc mẹ - con rõ ràng như sau:
      • <b>Tên Tài sản (VD: Vàng (Gold), Dầu (Oil), Bitcoin (BTC)):</b>
        - Mở: (loại kèo Mua/Bán, số lượng lệnh, vùng giá)
        - Chốt lời/Cắt lỗ: (thông tin giá nếu có)
        - Tình trạng: (nhận xét ngắn gọn)
    - Dùng dấu gạch ngang ( - ) cho các mục con thụt lề dưới mỗi kèo giao dịch.
    - Nội dung súc tích, đi thẳng vào vấn đề, không giải thích lằng nhằng.
    """

    try:
        response = summary_model.generate_content(prompt)
        # Làm sạch kết quả trả về: xóa các dấu markdown dư thừa nếu AI cố tình trả về
        clean_text = response.text.replace('**', '').replace('```html', '').replace('```', '').strip()
        return clean_text
    except Exception as e:
        return f"❌ Lỗi khi tải mô hình Gemini: {e}"

async def tomtat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Lấy tên lệnh mà user vừa gõ (ví dụ: '/tomtatbob' hoặc '/tomtatbob@LeviBot' -> 'tomtatbob')
    command_name = update.message.text.split()[0].split('@')[0].replace('/', '').lower()
    
    if command_name not in USER_COMMANDS:
         await update.message.reply_text("❌ Lệnh tóm tắt không hợp lệ.")
         return
         
    target_user = USER_COMMANDS[command_name]
    
    waiting_msg = await update.message.reply_text(f"⏳ Đang đi gom tin nhắn và tóm tắt cho @{target_user}, quá trình này mất khoảng 20-30 giây...")
    try:
        summary = await get_summary(target_user)
        
        # Chia nhỏ tin nhắn nếu dài quá 4000 ký tự (giới hạn của Telegram)
        if len(summary) > 4000:
            for i in range(0, len(summary), 4000):
                try:
                    await update.message.reply_text(summary[i:i+4000], parse_mode='HTML')
                except Exception:
                    await update.message.reply_text(summary[i:i+4000]) # Fallback nếu HTML bị lỗi
            await waiting_msg.delete()
        else:
            try:
                await waiting_msg.edit_text(summary, parse_mode='HTML')
            except Exception:
                await waiting_msg.edit_text(summary) # Fallback nếu HTML bị lỗi
            
    except Exception as e:
        logger.error(f"Lỗi khi tóm tắt tin nhắn: {e}")
        await waiting_msg.edit_text(f"❌ Có lỗi xảy ra: {e}")

async def send_daily_news(context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Hệ thống tự gọi hàm này vào 7:30 sáng hoặc gửi bù"""
    try:
        # 1. Lấy dữ liệu thị trường (như lệnh /wl)
        market_data = await asyncio.to_thread(get_market_data)
        
        t_gold_buy = market_data['gold_buy']
        t_gold_sell = market_data['gold_sell']
        if len(t_gold_buy) >= 7 and t_gold_buy.endswith('000'):
            t_gold_buy = t_gold_buy[:-3]
        if len(t_gold_sell) >= 7 and t_gold_sell.endswith('000'):
            t_gold_sell = t_gold_sell[:-3]

        now = datetime.now().strftime("%H:%M:%S")
        market_msg = (
            f"📊 *THỊ TRƯỜNG HÔM NAY* ({now})\n\n"
            f"🪙 *BTC* : ${market_data['btc']}\n"
            f"💵 *USDT*: Mua {market_data['usd_buy']} - Bán {market_data['usd_sell']}\n"
            f"🥇 *SJC* : Mua {t_gold_buy} - Bán {t_gold_sell}\n"
            f"🛢 *OIL* : ${market_data['oil']}\n"
            f"📈 *VNI* : {market_data['vni']}"
        )

        # 2. Lấy dữ liệu tin tức (như lệnh /tintuc)
        summary = await news_scraper.get_daily_summary()

        # Gộp cả 2 vào 1 tin nhắn
        full_msg = f"{market_msg}\n\n📰 *TÓM TẮT TIN TỨC*\n{summary}"

        await context.bot.send_message(chat_id=CHAT_ID, text=full_msg, parse_mode='Markdown', link_preview_options=LinkPreviewOptions(is_disabled=True))
        logger.info(f"Đã gửi bản tin AI và thông tin thị trường hàng ngày tới chat {CHAT_ID}")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi gửi bản tin tự động: {e}")
        return False

async def check_and_send_news(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kiểm tra cứ mỗi 60s xem đã qua 7h30 sáng chưa và hôm nay đã gửi chưa."""
    now = datetime.now()
    if now.hour > 7 or (now.hour == 7 and now.minute >= 30):
        today_str = now.strftime("%Y-%m-%d")
        last_sent_date = ""
        try:
            if os.path.exists("last_daily_news.txt"):
                with open("last_daily_news.txt", "r", encoding="utf-8") as f:
                    last_sent_date = f.read().strip()
        except Exception:
            pass
        
        if last_sent_date != today_str:
            logger.info(f"Chưa có bản tin nào được gửi cho ngày {today_str}. Tiến hành gửi bù/gửi chuẩn giờ...")
            # Ghi đè file ngay lập tức để chặn các job trùng lặp khởi chạy đồng thời
            try:
                with open("last_daily_news.txt", "w", encoding="utf-8") as f:
                    f.write(today_str)
            except Exception:
                pass
                
            success = await send_daily_news(context)
            if not success:
                # Xóa file hoặc rollback để nó thử lại vào 60s sau
                try:
                    if os.path.exists("last_daily_news.txt"):
                        os.remove("last_daily_news.txt")
                except Exception:
                    pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Chào bạn! Gõ lệnh /wl để xem giá các chỉ số thị trường nhé. Gõ /tintuc để tóm tắt báo hôm nay.\n\nCác lệnh tóm tắt tin nhắn:\n/tomtatsan - Tóm tắt kèo sếp San San\n/tomtatbob - Tóm tắt kèo sếp b0bby0ne\n/tomtatvinh - Tóm tắt kèo sếp trongvinhFA25 🤖")

def main() -> None:
    import sys
    is_hidden = False
    if sys.stdout is None:
        # Khi chạy bằng pythonw.exe, stdout và stderr là None, có thể làm crash asyncio / logging
        sys.stdout = open("bot_output.log", "a", encoding="utf-8")
        sys.stderr = open("bot_error.log", "a", encoding="utf-8")
        is_hidden = True
    else:
        sys.stdout.reconfigure(encoding='utf-8')

    handlers = [logging.FileHandler("bot.log", encoding='utf-8')]
    if not is_hidden:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
        level=logging.INFO,
        handlers=handlers
    )

    if not is_hidden:
        print("✅ Bot đang chạy! Nhấn Ctrl-C để dừng.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wl", wl_command))
    app.add_handler(CommandHandler("tintuc", news_command))
    
    # Đăng ký danh sách các lệnh tóm tắt
    app.add_handler(CommandHandler(list(USER_COMMANDS.keys()), tomtat_command))
    
    # Cấu hình báo thức tự động kiểm tra mỗi 60 giây
    # Nếu chưa gửi tin cho ngày hôm nay và đã >= 7h30 sáng, bot sẽ tự gửi
    job_queue = app.job_queue
    job_queue.run_repeating(check_and_send_news, interval=60, first=10)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
