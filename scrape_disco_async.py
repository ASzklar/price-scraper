import asyncio
from playwright.async_api import async_playwright

async def scrape_disco(busqueda, max_pages=5):
    url = f"https://www.disco.com.ar/{busqueda}?_q={busqueda}&map=ft"
    productos = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_selector("a.vtex-product-summary-2-x-clearLink", timeout=40000)

        for pagina in range(1, max_pages + 1):
            previous_height = 0
            while True:
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(1)
                current_height = await page.evaluate("document.body.scrollHeight")
                if current_height == previous_height:
                    break
                previous_height = current_height

            productos_raw = await page.query_selector_all("a.vtex-product-summary-2-x-clearLink")
            for producto in productos_raw:
                nombre_elem = await producto.query_selector("span.vtex-product-summary-2-x-productBrand")
                nombre = (await nombre_elem.inner_text()).strip() if nombre_elem else ""

                if busqueda.lower() not in nombre.lower():
                    continue

                precio_elem = await producto.query_selector("#priceContainer")
                if precio_elem:
                    precio = (await precio_elem.inner_text()).strip()
                else:
                    precio = "Sin precio"

                productos.append({
                    "nombre": nombre,
                    "precio": precio
                })

            siguiente_pagina_num = pagina + 1
            boton_siguiente = await page.query_selector(f'button[value="{siguiente_pagina_num}"]')

            if boton_siguiente:
                await boton_siguiente.click()
                await page.wait_for_timeout(4000)
                await page.wait_for_selector("a.vtex-product-summary-2-x-clearLink", timeout=40000)
            else:
                break

        await browser.close()

    return productos

if __name__ == "__main__":
    marca = "Not"
    resultados = asyncio.run(scrape_disco(marca))
    print(f"Se encontraron {len(resultados)} productos para la marca '{marca}':\n")
    for i, prod in enumerate(resultados, 1):
        print(f"{i}. {prod['nombre']} - Precio: {prod['precio']}")
