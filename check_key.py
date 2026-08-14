import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")

if key:
    print("Đã đọc được API key.")
    print("Độ dài key:", len(key))
    print("5 ký tự đầu:", key[:5])
else:
    print("KHÔNG đọc được API key.")