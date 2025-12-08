import ollama
import os

model = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")

res = ollama.chat(
    model=model,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Summarise the pros/cons of each platform."},
    ],
)

answer = res["message"]["content"]
