import asyncio
from playwright.async_api import async_playwright

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
                    all_productos.append({"nombre": nombre, "precio": precio})

            siguiente = await page.query_selector("a.page-link.page-back-next:has-text('Siguiente')")
            if siguiente and await siguiente.is_visible():
                clases = await siguiente.get_attribute("class")
                if clases and "disabled" in clases:
                    break
                await siguiente.click()
                await asyncio.sleep(5)
            else:
                break

        await browser.close()
    return all_productos

if __name__ == "__main__":
    marca = "Not"
    resultados = asyncio.run(scrape_coto_all_pages(marca))
    print(f"Se encontraron {len(resultados)} productos para la marca '{marca}':\n")
    for i, p in enumerate(resultados, 1):
        print(f"{i}. {p['nombre']} - Precio: {p['precio']}")
