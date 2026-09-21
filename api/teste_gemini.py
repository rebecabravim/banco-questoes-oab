import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

chave_api = os.getenv("GEMINI_API_KEY")

if not chave_api:
    raise ValueError("GEMINI_API_KEY não encontrada no arquivo .env")


cliente = genai.Client(api_key=chave_api)


resposta = cliente.models.generate_content(
    model="gemini-3.5-flash",
    contents="Explique em uma frase o que é Direito Constitucional."
)

print(resposta.text)