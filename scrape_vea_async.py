import asyncio
from playwright.async_api import async_playwright

async def scrape_vea_all_pages(busqueda):
    url = f"https://www.vea.com.ar/{busqueda}?_q={busqueda}&map=ft"
    productos = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"Abriendo URL: {url}")
        await page.goto(url)

        await page.wait_for_selector("div.vtex-product-summary-2-x-nameContainer", timeout=40000)

        async def scroll_to_bottom():
            last_count = 0
            scroll_position = 0
            retries = 0

            while True:
                await page.evaluate(f"window.scrollTo(0, {scroll_position});")
                await page.wait_for_timeout(1000)
                scroll_position += 500

                current_count = len(await page.query_selector_all("div.vtex-product-summary-2-x-nameContainer"))
                
                if current_count == last_count:
                    retries += 1
                    if retries >= 10:
                        break
                else:
                    retries = 0
                    last_count = current_count

        await scroll_to_bottom()
        await page.wait_for_timeout(2000)

        productos_en_pagina = await page.query_selector_all("div.vtex-product-summary-2-x-nameContainer")

        for producto_div in productos_en_pagina:
            nombre_span = await producto_div.query_selector("span.vtex-product-summary-2-x-productBrand")
            nombre = await nombre_span.inner_text() if nombre_span else "Sin nombre"
            nombre = nombre.strip()

            if busqueda.lower() not in nombre.lower():
                continue

            contenedor = await producto_div.evaluate_handle("node => node.closest('section')")
            if contenedor:
                precio_elem = await contenedor.query_selector("div#priceContainer")
                precio = await precio_elem.inner_text() if precio_elem else "Sin precio"
                precio = precio.strip()
            else:
                precio = "Sin precio"

            productos.append({
                "nombre": nombre,
                "precio": precio
            })

        await browser.close()

    return productos

if __name__ == "__main__":
    marca = "not"
    resultados = asyncio.run(scrape_vea_all_pages(marca))
    print(f"Se encontraron {len(resultados)} productos para la marca '{marca}':\n")
    for i, prod in enumerate(resultados, 1):
        print(f"{i}. {prod['nombre']} - Precio: {prod['precio']}")
