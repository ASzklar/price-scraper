import json
from curl_cffi import requests

HEADERS = {
    "Accept": "application/json",
    "Accept-Language": "es-AR,es;q=0.9",
    "Referer": "https://www.disco.com.ar/",
}

def _formatear_precio(valor: float) -> str:
    entero = int(valor)
    decimales = round((valor - entero) * 100)
    entero_fmt = f"{entero:,}".replace(",", ".")
    return f"${entero_fmt},{decimales:02d}"

def _fetch_page(termino: str, desde: int, hasta: int) -> list:
    url = (
        f"https://www.disco.com.ar/api/catalog_system/pub/products/search"
        f"?ft={requests.utils.quote(termino)}&_from={desde}&_to={hasta}"
    )
    resp = requests.get(url, headers=HEADERS, impersonate="chrome124", timeout=20)
    resp.raise_for_status()
    return resp.json()

async def scrape_disco(busqueda: str, max_pages: int = 5):
    productos = []
    page_size = 50
    termino_lower = busqueda.lower()

    for pagina in range(max_pages):
        desde = pagina * page_size
        hasta = desde + page_size - 1
        try:
            data = _fetch_page(busqueda, desde, hasta)
        except Exception as e:
            print(f"[Disco] Error en pagina {pagina + 1}: {e}")
            break

        for item in data:
            brand = item.get("brand", "")
            if termino_lower not in brand.lower():
                continue

            nombre = item.get("productName", "").strip()
            precio_val = None
            items = item.get("items", [])
            if items:
                sellers = items[0].get("sellers", [])
                if sellers:
                    offer = sellers[0].get("commertialOffer", {})
                    if offer.get("AvailableQuantity", 0) > 0:
                        precio_val = offer.get("Price")

            if precio_val is not None:
                productos.append({
                    "nombre": nombre,
                    "precio": _formatear_precio(precio_val),
                })

        print(f"[Disco] Pagina {pagina + 1}: {len(data)} resultados de API")
        if len(data) < page_size:
            break

    return productos

if __name__ == "__main__":
    import asyncio
    marca = "Not"
    resultados = asyncio.run(scrape_disco(marca))
    print(f"\nSe encontraron {len(resultados)} productos para '{marca}':\n")
    for i, prod in enumerate(resultados, 1):
        print(f"{i:2d}. {prod['nombre']} - {prod['precio']}")
