import os

import requests
from dotenv import load_dotenv

load_dotenv()

PROVIDERS = {
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "modelo_default": "llama-3.1-8b-instant",
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "modelo_default": "meta-llama/llama-3.1-8b-instruct:free",
    },
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "modelo_default": "gemini-1.5-flash",
    },
}

SYSTEM_PROMPT = (
    "Tu única tarea es reformular un texto ya escrito para que suene cordial y breve — "
    "nunca más de una oración corta, sin rodeos ni agregados de más. "
    "El texto es la respuesta de un chatbot de precios de supermercado. "
    "No inventes ni modifiques ningún número, precio, nombre de producto o "
    "supermercado que aparezca en el texto — usá exactamente los mismos datos, "
    "solo mejorá la redacción. No agregues información que no esté en el texto original, "
    "aunque la sepas o la pregunta del usuario sea sobre otro tema: nunca respondas la "
    "pregunta por tu cuenta, solo reformulá el texto dado. "
    "No menciones tu propio nombre ni inventes marcas o supermercados que no estén ya en "
    "el texto. No envuelvas la respuesta entre comillas. Respondé siempre en español."
)


def rephrase(respuesta, pregunta):
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not provider or not api_key or provider not in PROVIDERS:
        return respuesta

    config = PROVIDERS[provider]
    modelo = os.getenv("LLM_MODEL", config["modelo_default"])

    try:
        resp = requests.post(
            config["url"],
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": modelo,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Pregunta del usuario: {pregunta}\nRespuesta calculada: {respuesta}",
                    },
                ],
                "temperature": 0.4,
                "max_tokens": 90,
            },
            timeout=8,
        )
        resp.raise_for_status()
        texto = resp.json()["choices"][0]["message"]["content"].strip()
        texto = _quitar_comillas_envolventes(texto)
        return texto or respuesta
    except Exception:
        return respuesta


def _quitar_comillas_envolventes(texto):
    pares = (('"', '"'), ("'", "'"), ("«", "»"), ("“", "”"))
    for apertura, cierre in pares:
        if texto.startswith(apertura) and texto.endswith(cierre) and len(texto) > 1:
            return texto[1:-1].strip()
    return texto
