# Veganito — Chatbot de precios veganos

Trabajo Práctico Integrador — chatbot que responde preguntas en lenguaje natural sobre
precios reales de 3 marcas veganas (NotCo, Vegetalex, Felices Las Vacas) en 6
supermercados argentinos, usando los datos históricos del proyecto
[Price-Scraper](..).

## Arquitectura

```
Usuario → Interfaz web (HTML+CSS+JS) → FastAPI (/chat) → Pandas → respuesta
```

- `data.py`: carga `data/precios_historico.csv` y `data/supermercados.csv`, limpia
  duplicados y nulos, hace un `merge()` entre ambos archivos, y calcula columnas nuevas
  (promedio histórico por producto, variación % respecto a ese promedio) con `groupby`.
- `nlu.py`: detecta la intención de la pregunta (fuzzy matching con `fuzzywuzzy`, tolera
  distintas formas de preguntar lo mismo) y extrae qué producto/supermercado/marca se
  menciona.
- `responder.py`: una función por intención, calcula la respuesta con Pandas.
- `llm.py`: opcional — si configurás una API key, reformula la respuesta con un modelo de
  lenguaje (Groq por default). Sin key, el chatbot funciona igual, solo que con la
  redacción tal cual la genera Pandas.
- `main.py`: la API FastAPI y el server de los archivos estáticos del frontend.

## Instalación

```bash
cd chatbot
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Generar los datos

Los CSVs en `data/` ya vienen generados, pero si el scraper juntó datos nuevos podés
regenerarlos desde la raíz del repo:

```bash
cd ..
python build_dataset.py
```

## Ejecutar

```bash
cd chatbot
.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Abrí `http://localhost:8000` en el navegador.

## Activar el bonus de IA (opcional)

```bash
cp .env.example .env
```

Completá `LLM_API_KEY` con una key de [Groq](https://console.groq.com/keys) (gratis).
Sin este paso, el chatbot funciona exactamente igual, sin la reformulación de IA.

## Preguntas de ejemplo

- ¿Cuál es el producto más barato hoy?
- ¿Dónde es más barato el Not Milk?
- ¿Cuál es el precio promedio histórico de la Milanesa de Soja Vegetalex Tradicional 340g?
- ¿Cómo varió el precio de X en el tiempo?
- ¿Qué conviene comprar hoy?
- ¿Cuántos productos hay de la marca Vegetalex?

Distintas formas de preguntar lo mismo (ej. "¿dónde es más barato X?" vs "¿qué
supermercado tiene el menor precio de X?") deberían dar la misma respuesta.
