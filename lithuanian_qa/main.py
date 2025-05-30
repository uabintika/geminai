import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from getpass import getpass

# Load environment variables from .env file
load_dotenv()

token = os.getenv("AIKEY")
endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1-nano"


# API key and custom endpoint
#api_key = os.getenv("OPENAI_API_KEY") or getpass("Enter your AI key: ")
#endpoint = "https://api.openai.com/v1"  # Custom GitHub OpenAI-compatible endpoint
#model = "gpt-3.5-turbo"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)

# Pydantic model for language detection
class LithuanianQuestionCheck(BaseModel):
    is_lithuanian_language: bool


# Step 1: Detect if the question is in Lithuanian
def is_lithuanian(question: str) -> bool:
    system_prompt = (
        "You are a language detection assistant. "
        "Answer only `true` if the user's message is in Lithuanian, or `false` otherwise."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0,
            top_p=1.0,
        )

        reply = response.choices[0].message.content.strip().lower()
        return reply == "true"
    except Exception as e:
        print("Error during language detection:", e)
        return False



# Step 2: Answer the question in Lithuanian
def answer_question(question: str) -> str:
    system_prompt = (
        "Atsakyk į klausimą lietuvių kalba kuo aiškiau ir trumpiau. "
        "Jei klausimas nėra aiškus, paklausk patikslinimo."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            top_p=1.0,
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Klaida atsakant į klausimą: {e}"


# Step 3: Main script logic
def main():
    print("Sveiki! Įveskite klausimą. Norėdami išeiti, rašykite 'exit'.")

    while True:
        question = input("Klausimas: ").strip()
        if question.lower() == "exit":
            print("Iki pasimatymo!")
            break

        if is_lithuanian(question):
            answer = answer_question(question)
            print(f"Atsakymas: {answer}")
        else:
            print("Klausimas nėra lietuvių kalba. Bandykite dar kartą lietuviškai.")


if __name__ == "__main__":
    main()
