import requests
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("BRAWL_API_TOKEN")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

tag = "%238QV90CYQ"
url = f"https://api.brawlstars.com/v1/players/{tag}/battlelog"

resposta = requests.get(url, headers=HEADERS)
print("Status:", resposta.status_code)
print("Resposta:", resposta.json())

battlelog = resposta.json()
print(battlelog[0])