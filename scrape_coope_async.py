import re
import asyncio
from playwright.async_api import async_playwright

_NOTCO_RE = re.compile(
    r'\bnot(?:co|milk|burger|burguer|mila|chicken|chorixo|protein|cream|cheese|salxicha|creamcheese)\b'
    r'|\bnot\s+(?:milk|burger|mila|chicken|chorixo|protein|cream|cheese|co\b)',
    re.IGNORECASE
)

async def scrape_coope(busqueda, max_pages=5):
    url = "https://www.lacoopeencasa.coop/"
    productos = []
    vistos = set()
    if busqueda.lower() == "not":
        patron = _NOTCO_RE
    else:
        patron = re.compile(r'\b' + re.escape(busqueda), re.IGNORECASE)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_selector("input#idInputBusqueda")
        await page.fill("input#idInputBusqueda", busqueda)
        await page.keyboard.press("Enter")
        await asyncio.sleep(4)
        await page.wait_for_selector("div.card-content", timeout=40000)
        await asyncio.sleep(2)

        for _ in range(max_pages):
            previous_height = 0
            while True:
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(1)
                current_height = await page.evaluate("document.body.scrollHeight")
                if current_height == previous_height:
                    break
                previous_height = current_height

            cards = await page.query_selector_all("div.card-content")
            for card in cards:
                nombre_elem = await card.query_selector("div.card-descripcion p.text-capitalize")
                nombre = await nombre_elem.inner_text() if nombre_elem else ""
                nombre = nombre.strip()

                nombre_minuscula = nombre.lower()
                if patron.search(nombre) is None:
                    continue

                precio_entero = await card.query_selector("div.precio-entero")
                precio_decimal = await card.query_selector("div.precio-decimal")

                precio_text = ""
                if precio_entero:
                    precio_text = (await precio_entero.inner_text()).strip().lstrip("$").strip()

                if precio_decimal:
                    precio_text += "," + (await precio_decimal.inner_text()).strip()
                else:
                    precio_text += ",00"

                precio = "$" + precio_text.replace(" ", "")

                if nombre not in vistos:
                    vistos.add(nombre)
                    productos.append({
                        "nombre": nombre,
                        "precio": precio
                    })

            btn_siguiente = await page.query_selector("ul.pagination li.waves-effect svg use[href*='derecha']")
            if btn_siguiente:
                btn_siguiente_parent = await btn_siguiente.evaluate_handle("node => node.closest('li')")
                if btn_siguiente_parent:
                    await btn_siguiente_parent.click()
                    await page.wait_for_timeout(4000)
                    await page.wait_for_selector("div.card-content", timeout=40000)
                else:
                    break
            else:
                break

        await browser.close()

    return productos

if __name__ == "__main__":
    marca = "Vegetalex"
    resultados = asyncio.run(scrape_coope(marca))
    print(f"Se encontraron {len(resultados)} productos para la marca '{marca}':\n")
    for i, prod in enumerate(resultados, 1):
        print(f"{i}. {prod['nombre']} - Precio: {prod['precio']}")
