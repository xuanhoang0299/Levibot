# Levi Telegram Bot

Bot Telegram (Levi Bot) là một trợ lý ảo hỗ trợ thông báo giá cả tự động, tổng hợp tin tức từ các kênh Telegram và tóm tắt kèo/nhận định thị trường của các chuyên gia bằng AI.

## Các tính năng chính

- **Báo giá danh mục đầu tư (`/wl`)**: Cập nhật giá Vàng trong nước (SJC, Bảo Tín Minh Châu), Vàng Thế giới, Dầu, BTC, USDT P2P, và VN-Index.
- **Tóm tắt tin tức (`/tintuc`)**: Tự động gom kịch bản tin nhắn trong vòng 24h từ kênh cấu hình và dùng Gemini AI tóm tắt những tin tức nổi bật.
- **Tóm tắt kèo chuyên gia**: Lọc riêng tin nhắn của một số tài khoản chuyên gia trong group, tóm tắt kèo giao dịch (điểm vào, chốt lời, cắt lỗ) thông qua sức mạnh của AI. (Các lệnh `/tomtatsan`, `/tomtatbob`, `/tomtatvinh`).
- **Gửi bản tin sáng tự động**: Thiết lập bot tự động lấy giá tổng hợp và AI tóm tắt tin tức để gửi vào một Chat ID cố định mỗi ngày vào lúc 7:30 sáng.

## Chuẩn bị cấu hình

Để chạy được bot này trên thiết bị của bạn, bạn cần có các điều kiện sau:

1. Có cài đặt **Python** (phiên bản 3.9 trở lên).
2. Có Bot Token từ [BotFather Telegram](https://t.me/BotFather).
3. Đăng ký tài khoản lập trình viên Telegram tại [my.telegram.org](https://my.telegram.org) để lấy `API_ID` và `API_HASH` (Dùng cho tính năng đọc tin nhắn tự động từ tài khoản người dùng).
4. Lấy API Key miễn phí của bộ não sinh tạo AI Gemini tại [Google AI Studio](https://aistudio.google.com/).

## Hướng dẫn cài đặt và chạy Bot

**Bước 1: Tải mã nguồn**
Mở Terminal (hoặc CMD/PowerShell), gõ lệnh sau để tải toàn bộ mã nguồn về máy:
```bash
git clone https://github.com/xuanhoang0299/Levibot.git
cd Levibot
```

**Bước 2: Cài đặt thư viện**
Chạy lệnh sau để cài đặt các thư viện cần dùng (lưu ý: trên MacOS/Linux có thể dùng `pip3` thay thế `pip`):
```bash
pip install -r requirements.txt
```

**Bước 3: Tạo file cấu hình bảo mật (.env)**
Mã nguồn bạn vừa tải về đi kèm một file tên là `.env.example`.
- Bạn hãy sao chép (copy) file `.env.example` và đổi tên nó thành `.env`.
- Mở file `.env` lên bằng trình soạn thảo mã yêu thích và điền các Key bí mật của bạn vào đó:
```env
BOT_TOKEN=85419...:AAHuB...
CHAT_ID=-4668...
TELEGRAM_API_ID=350...
TELEGRAM_API_HASH=63045...
GEMINI_API_KEY_1=AIzaSy...
GEMINI_API_KEY_2=AIzaSy...
```

**Bước 4: Đăng nhập tài khoản Telethon (QUAN TRỌNG - CHỈ LÀM LẦN ĐẦU)**
Vì Bot sử dụng Telethon để hoạt động như một User trên máy nhằm đọc tin tức, bạn cần cấp phép cho việc này.
- Mở Terminal và bắt buộc chạy lệnh này thủ công ở lần đầu tiên:
```bash
python news_scraper.py
```
- Khi chạy, Terminal sẽ yêu cầu bạn nhập **Số điện thoại** tài khoản Telegram (nhớ có mã vùng, ví dụ: `+8498...`).
- Sau đó, Telegram sẽ gửi cho bạn 1 mã Code. Hãy nhập dãy số Code đó vào Terminal.
- Nếu thành công, mã nguồn sẽ in ra thông báo, đồng thời sinh ra một file `.session` ở thư mục dự án (file này tự động bị bỏ qua nhờ `.gitignore` để đảm bảo an toàn).

**Bước 5: Khởi chạy Bot**
Cuối cùng, chạy file chính để vận hành Bot:
```bash
python market_bot.py
```
- Bạn có thể vào Telegram gõ lệnh `/start` đối với con bot, sau đó thử các lệnh như `/wl` để kiểm tra.

## Cấu trúc dự án
- `market_bot.py`: Quản lý tác vụ chính, lấy giá thị trường (API ngoài, cào HTML), và các lệnh Telegram chung.
- `news_scraper.py`: Quản lý việc đọc bản tin 24h và tóm tắt theo thời gian biểu bằng Gemini AI.
- `crypto_bot.py`: Báo giá thị trường tiền điện tử từ CoinGecko và tin tức tiếng Anh CryptoCompare.
- `TeleMessSummary.py`: Xử lý chuyên sâu đọc tin nhắn của các tài khoản chuyên gia (Trader).

## Tác giả / Bản quyền
Dự án được phát triển và duy trì bởi nhà phát triển Levi Bot. Mọi sao chép trái phép hãy cẩn thận =))
