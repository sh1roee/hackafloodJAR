from fastapi import FastAPI
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Configure OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

@app.get("/")
def root():
    return {"message": "Hello, World!"}

@app.get("/test-gpt")
def test_gpt():
    # test endpoint to make a prompt to GPT-4
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "What is the capital of France?"}
            ]
        )
        
        answer = response.choices[0].message.content
        
        return {
            "prompt": "What is the capital of France?",
            "answer": answer,
            "model": "gpt-4"
        }
    except Exception as e:
        return {"error": str(e)}