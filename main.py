from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import cloudscraper
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import random

# --- Cargar variables del .env ---
load_dotenv()

URL_BASE = os.getenv("URL_BASE")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI(title="RUT Scraper API")

# --- Modelo de request ---
class RutRequest(BaseModel):
    rut: str

# --- Función para obtener nombre por RUT ---
def obtener_nombre_por_rut(rut: str) -> str:
    scraper = cloudscraper.create_scraper()

    # Ajustar User-Agent y headers
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    payload = {"term": rut}

    response = scraper.post(URL_BASE, data=payload, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error al obtener datos de la página")

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="table-hover")
    if not table or not table.tbody.find("tr"):
        raise HTTPException(status_code=404, detail="No se encontró información para ese RUT")

    first_row = table.tbody.find("tr")
    nombre = first_row.find("td").get_text(strip=True)
    return nombre

@app.get("/")
def read_root():
    return {"message": "Hola, FastAPI está funcionando 🚀"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# --- Endpoint de la API ---
@app.post("/consultar_nombre")
def consultar_nombre(request: RutRequest):
    nombre = obtener_nombre_por_rut(request.rut)
    return {"rut": request.rut, "nombre": nombre}

# --- Middleware para manejar errores ---
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))