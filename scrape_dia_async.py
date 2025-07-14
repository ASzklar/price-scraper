import asyncio
from playwright.async_api import async_playwright

async def scrape_dia(marca):
    url = f"https://diaonline.supermercadosdia.com.ar/{marca.lower()}?_q={marca}&map=ft"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        ))
        page = await context.new_page()
        await page.goto(url)

        viewport_height = await page.evaluate("window.innerHeight")
        scroll_height = await page.evaluate("document.body.scrollHeight")
        scroll_position = 0
        while scroll_position < scroll_height:
            scroll_position += viewport_height // 2
            await page.evaluate(f"window.scrollTo(0, {scroll_position})")
            await asyncio.sleep(1)
            scroll_height = await page.evaluate("document.body.scrollHeight")

        await page.wait_for_selector("div.vtex-product-summary-2-x-nameContainer span.vtex-product-summary-2-x-productBrand", timeout=30000)

        productos = await page.query_selector_all("div.vtex-product-summary-2-x-nameContainer span.vtex-product-summary-2-x-productBrand")
        precios = await page.query_selector_all("div.pr0.items-stretch.flex span.diaio-store-5-x-sellingPriceValue")

        all_productos = []
        for i in range(min(len(productos), len(precios))):
            nombre = (await productos[i].inner_text()).strip()
            precio = (await precios[i].inner_text()).strip()

            # Filtro condicional solo para "felices las vacas"
            if marca.lower() == "felices las vacas":
                if "felices las vacas" not in nombre.lower():
                    continue  # Ignorar producto que no menciona la marca

            all_productos.append({"nombre": nombre, "precio": precio})

        await browser.close()
    return all_productos

if __name__ == "__main__":
    marca = "Not"
    resultados = asyncio.run(scrape_dia(marca))
    print(f"Se encontraron {len(resultados)} productos para la marca '{marca}':\n")
    for i, p in enumerate(resultados, 1):
        print(f"{i}. {p['nombre']} - Precio: {p['precio']}")
