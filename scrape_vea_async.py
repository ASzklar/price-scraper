import asyncio
from playwright.async_api import async_playwright

# Términos de búsqueda específicos por marca, porque "Not" es demasiado genérico en Vea
TERMINOS_POR_MARCA = {
    "not": ["Notburger", "Notmilk", "Notmila", "Notchicken", "Notchorixo", "Notprotein"],
    "vegetalex": ["Vegetalex"],
    "felices las vacas": ["Felices Las Vacas", "Jogurtti"],
}

async def _scrape_termino(page, termino: str, marca_lower: str) -> list:
    url = f"https://www.vea.com.ar/{termino}?_q={termino}&map=ft"
    print(f"[Vea] Buscando: {termino}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"[Vea] Error navegando a {termino}: {e}")
        return []

    try:
        await page.wait_for_selector("div.vtex-product-summary-2-x-nameContainer", timeout=20000)
    except:
        print(f"[Vea] Sin resultados para: {termino}")
        return []

    # Scroll para cargar todos los productos
    last_count = 0
    retries = 0
    scroll_pos = 0
    while True:
        await page.evaluate(f"window.scrollTo(0, {scroll_pos});")
        await page.wait_for_timeout(800)
        scroll_pos += 500
        current_count = len(await page.query_selector_all("div.vtex-product-summary-2-x-nameContainer"))
        if current_count == last_count:
            retries += 1
            if retries >= 8:
                break
        else:
            retries = 0
            last_count = current_count

    productos_en_pagina = await page.query_selector_all("div.vtex-product-summary-2-x-nameContainer")
    resultados = []

    for producto_div in productos_en_pagina:
        nombre_span = await producto_div.query_selector("span.vtex-product-summary-2-x-productBrand")
        nombre = (await nombre_span.inner_text()).strip() if nombre_span else ""

        if not nombre or marca_lower not in nombre.lower():
            continue

        contenedor = await producto_div.evaluate_handle("node => node.closest('section')")
        precio = "Sin precio"
        if contenedor:
            precio_elem = await contenedor.query_selector("div#priceContainer")
            if precio_elem:
                precio = (await precio_elem.inner_text()).strip()

        resultados.append({"nombre": nombre, "precio": precio})

    print(f"[Vea] {termino}: {len(resultados)} productos encontrados")
    return resultados

async def scrape_vea_all_pages(busqueda: str):
    marca_lower = busqueda.lower()
    terminos = TERMINOS_POR_MARCA.get(marca_lower, [busqueda])
    todos = []
    vistos = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="es-AR",
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "es-AR,es;q=0.9",
            }
        )
        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        for termino in terminos:
            resultados = await _scrape_termino(page, termino, marca_lower)
            for prod in resultados:
                if prod["nombre"] not in vistos:
                    vistos.add(prod["nombre"])
                    todos.append(prod)
            await asyncio.sleep(2)

        await browser.close()

    return todos

if __name__ == "__main__":
    marca = "Not"
    resultados = asyncio.run(scrape_vea_all_pages(marca))
    print(f"\nSe encontraron {len(resultados)} productos para '{marca}':\n")
    for i, prod in enumerate(resultados, 1):
        print(f"{i:2d}. {prod['nombre']} - {prod['precio']}")
