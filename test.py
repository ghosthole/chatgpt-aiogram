import os
import openai
from dotenv import load_dotenv


load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")

completion = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "user", "content": "What is football?"}
  ]
)

print(completion.choices[0].message.content)
