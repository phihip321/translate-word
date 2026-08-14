from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Hãy nói xin chào bằng tiếng Việt."
)

print(response.text)