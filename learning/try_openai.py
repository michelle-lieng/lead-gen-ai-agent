from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

prompt = f"""
You are a cat. Say hello.
"""

response = client.responses.create(
    model="gpt-3.5-turbo",
    input=prompt
)

print(response.output_text)