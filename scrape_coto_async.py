import re
import asyncio
from playwright.async_api import async_playwright

_NOTCO_RE = re.compile(
    r'\bnot(?:co|milk|burger|burguer|mila|chicken|chorixo|protein|cream|cheese|salxicha|creamcheese)\b'
    r'|\bnot\s+(?:milk|burger|mila|chicken|chorixo|protein|cream|cheese|co\b)',
    re.IGNORECASE
)

def _es_producto_de_marca(nombre: str, marca: str) -> bool:
    if marca.lower() == "not":
        return bool(_NOTCO_RE.search(nombre))
    patron = re.compile(r'\b' + re.escape(marca), re.IGNORECASE)
    return bool(patron.search(nombre))

async def scrape_coto_all_pages(marca):
    url = f"https://www.cotodigital.com.ar/sitios/cdigi/categoria?_dyncharset=utf-8&Dy=1&Ntt={marca}&idSucursal=200"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            "--disable-blink-features=AutomationControlled",
        ])
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        ))
        page = await context.new_page()
        await page.goto(url)
        await asyncio.sleep(5)

        all_productos = []

        pagina_actual = 1

        while True:
            try:
                await page.wait_for_selector("div.centro-precios", timeout=40000)
            except:
                break

            productos = await page.query_selector_all("div.centro-precios")
            for producto in productos:
                nombre_elem = await producto.query_selector("h3.nombre-producto")
                precio_elem = await producto.query_selector("h4.card-title")
                if nombre_elem and precio_elem:
                    nombre = (await nombre_elem.inner_text()).strip()
                    precio = (await precio_elem.inner_text()).strip()
                    if _es_producto_de_marca(nombre, marca):
                        all_productos.append({"nombre": nombre, "precio": precio})

            print(f"[Coto] Pagina {pagina_actual}: {len(productos)} productos")

            # Obtener todos los numeros de pagina disponibles
            page_links = await page.query_selector_all("a.pages-link")
            numeros = []
            for link in page_links:
                texto = (await link.inner_text()).strip()
                if texto.isdigit():
                    numeros.append(int(texto))

            proxima = pagina_actual + 1
            if proxima not in numeros:
                break

            # Hacer click en el numero de pagina siguiente
            link_siguiente = None
            for link in page_links:
                texto = (await link.inner_text()).strip()
                if texto == str(proxima):
                    link_siguiente = link
                    break

            if not link_siguiente:
                break

            try:
                await page.wait_for_selector("ngx-spinner", state="hidden", timeout=10000)
            except:
                pass

            await link_siguiente.dispatch_event("click")
            await asyncio.sleep(5)
            pagina_actual = proxima

        await browser.close()
    return all_productos

if __name__ == "__main__":
    marca = "Not"
    resultados = asyncio.run(scrape_coto_all_pages(marca))
    print(f"Se encontraron {len(resultados)} productos para la marca '{marca}':\n")
    for i, p in enumerate(resultados, 1):
        print(f"{i}. {p['nombre']} - Precio: {p['precio']}")
