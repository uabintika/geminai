import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
import requests

load_dotenv()

# OpenAI
token = os.getenv("AIKEY")
endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1-nano"

# Weather
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
LOCATION_FILE = "location.txt"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)

class LithuanianQuestionCheck(BaseModel):
    is_lithuanian_language: bool


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
        )
        reply = response.choices[0].message.content.strip().lower()
        return reply == "true"
    except Exception as e:
        print("Klaida tikrinant kalbą:", e)
        return False


# Weather functions
def get_stored_location():
    if os.path.exists(LOCATION_FILE):
        with open(LOCATION_FILE, "r", encoding="utf-8") as file:
            return file.read().strip()
    return None

def store_location(location: str):
    with open(LOCATION_FILE, "w", encoding="utf-8") as file:
        file.write(location)

def ask_location():
    location = input("Įveskite savo vietovę (pvz., Vilnius): ").strip()
    store_location(location)
    return location

def choose_location():
    current_location = get_stored_location()
    if current_location:
        print(f"Jūsų ankstesnė vietovė: {current_location}")
        choice = input("Ar patikrinti orą šios vietovės? (taip/ne): ").strip().lower()
        if choice == "taip":
            return current_location
    return ask_location()

def get_weather(location: str):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units=metric&lang=lt"
    )
    try:
        response = requests.get(url)
        data = response.json()

        if data.get("cod") != 200:
            return f"Klaida: {data.get('message', ' - nežinoma klaida')}"
        
        weather_summary = data["weather"][0]["description"]
        actual_temperature = round(data["main"]["temp"])
        feels_like = round(data["main"]["feels_like"])
        wind_speed = round(data["wind"]["speed"])

        return f"Orų informacija - {location}: {weather_summary}, {actual_temperature} laipsnių (jutiminė temperatūra - {feels_like} laipsnių). Vėjo greitis: {wind_speed} m/s."
    except Exception as e:
        return f"Klaida: {e}"


# OpenAI functions
def answer_question(question: str) -> str:
    if "oras" in question.lower():
        location = choose_location()
        return get_weather(location)

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
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Klaida atsakant į klausimą: {e}"


# Main function
def main():
    print("Sveiki! Įveskite klausimą. Norėdami išeiti, rašykite 'bye'.")
    print("Norėdami sužinoti orų informaciją - parašykite 'oras'")
    while True:
        question = input("Klausimas: ").strip()
        if question.lower() == "bye":
            print("Iki pasimatymo!")
            break

        if is_lithuanian(question):
            answer = answer_question(question)
            print(f"Atsakymas: {answer}")
        else:
            print("Klausimas nėra lietuvių kalba. Bandykite dar kartą lietuviškai.")

if __name__ == "__main__":
    main()
