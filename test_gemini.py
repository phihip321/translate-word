from dotenv import load_dotenv
from google import genai

load_dotenv()

print("1. Đang kết nối Gemini...")

client = genai.Client()

print("2. Đang gửi câu hỏi...")

interaction = client.interactions.create(
    model="gemini-3.5-flash",
    input="Hãy trả lời đúng một câu: Xin chào!",
    generation_config={
        "thinking_level": "minimal"
    }
)

print("3. Gemini đã trả lời:")
print(interaction.output_text)