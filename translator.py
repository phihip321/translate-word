import socket
from dotenv import load_dotenv
from google import genai

# IPv4
old_getaddrinfo = socket.getaddrinfo

def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return old_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

socket.getaddrinfo = getaddrinfo_ipv4

# Gemini
load_dotenv()
client = genai.Client()


# Hàm dịch
def translate(text, source, target):

    prompt = f"""
Bạn là một phiên dịch viên chuyên nghiệp.

Hãy dịch văn bản từ {source} sang {target}.

Yêu cầu:
- Dịch chính xác.
- Văn phong tự nhiên.
- Không giải thích.
- Chỉ trả về bản dịch.

Văn bản:
{text}
"""

    interaction = client.interactions.create(
        model="gemini-3.5-flash",
        input=prompt,
        generation_config={
            "thinking_level": "minimal"
        }
    )

    return interaction.output_text


# Chương trình chính

source = input("Ngôn ngữ nguồn: ")
target = input("Ngôn ngữ đích: ")
text = input("Nhập văn bản cần dịch: ")

print()
print("Đang dịch...")

result = translate(text, source, target)

print()
print("===== BẢN DỊCH =====")
print(result)