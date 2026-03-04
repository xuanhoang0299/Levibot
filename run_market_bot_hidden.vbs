Set objShell = CreateObject("WScript.Shell")
' Chuyển hướng thư mục làm việc để Python nhận diện đúng đường dẫn tương đối
objShell.CurrentDirectory = "d:\CODE\BotProject"
' Chạy file pythonw.exe (môi trường ảo) để chạy ngầm không hiện cửa sổ command line
objShell.Run """d:\CODE\.venv\Scripts\pythonw.exe"" ""d:\CODE\BotProject\market_bot.py""", 0, False
