from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from data import get_datos
from llm import rephrase
from responder import RESPUESTAS_SIN_DATOS, responder

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Veganito - Chatbot de precios veganos")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.middleware("http")
async def no_cache_estaticos(request, call_next):
    # Sin esto, el navegador cachea app.js/style.css y no siempre los vuelve
    # a pedir con un refresh normal, mostrando una versión vieja del chatbot.
    response = await call_next(request)
    if request.url.path.startswith("/static/") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-store"
    return response


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    datos = get_datos()
    respuesta = responder(datos, body.question)
    # Si la respuesta no tiene datos reales todavía (no reconocimos la
    # pregunta, o falta que aclaren qué producto), no se la mandamos al LLM:
    # no hay nada que mejorar, y un modelo chico puede terminar inventando
    # un producto/supermercado de la nada para sonar más natural.
    if respuesta not in RESPUESTAS_SIN_DATOS:
        respuesta = rephrase(respuesta, body.question)
    return ChatResponse(answer=respuesta)
