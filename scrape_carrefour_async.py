import asyncio
from playwright.async_api import async_playwright

async def scrape_carrefour_marca(marca: str):
    base_url = f"https://www.carrefour.com.ar/{marca}?_q={marca}&map=ft&page={{}}"
    all_products = []
    seen_product_names = set()

    async def scroll_para_cargar_suave(page):
        """Scroll más suave y gradual"""
        # Hacer scroll gradual hasta el final
        for i in range(10):
            await page.mouse.wheel(0, 800)
            await asyncio.sleep(1.5)
        
        # Scroll final hasta abajo
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)
        
        # Volver arriba para procesar
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Configurar timeouts más conservadores
        page.set_default_timeout(15000)

        current_page = 1
        max_pages = 10  # Límite de seguridad
        
        while current_page <= max_pages:
            url = base_url.format(current_page)
            print(f"\n🌐 Visitando página {current_page}: {url}")
            
            try:
                # Navegación simple sin networkidle
                await page.goto(url, timeout=20000)
                await asyncio.sleep(3)
                
            except Exception as e:
                print(f"❌ Error cargando página {current_page}: {e}")
                break
            
            # Intentar encontrar la galería
            try:
                await page.wait_for_selector("div.valtech-carrefourar-search-result-3-x-gallery", timeout=15000)
            except:
                print("❌ Galería no encontrada")
                break

            # Realizar scroll suave
            await scroll_para_cargar_suave(page)

            # Buscar productos
            products = page.locator("div.valtech-carrefourar-search-result-3-x-gallery > div > section > a")
            count = await products.count()

            if count == 0:
                break

            # Procesar productos
            products_processed = 0
            for i in range(count):
                product = products.nth(i)
                try:
                    # Obtener nombre
                    name = "Nombre no disponible"
                    try:
                        name_element = product.locator("span.vtex-product-summary-2-x-productBrand")
                        if await name_element.count() > 0:
                            name = await name_element.inner_text(timeout=5000)
                            name = name.strip()
                    except:
                        pass

                    # Obtener precio
                    price = "Precio no disponible"
                    try:
                        price_spans = product.locator("span.valtech-carrefourar-product-price-0-x-currencyContainer")
                        count_prices = await price_spans.count()
                        
                        for j in range(count_prices):
                            span = price_spans.nth(j)
                            classes = await span.evaluate("e => e.className")
                            parent_classes = await span.evaluate("e => e.parentElement.className")
                            
                            if "strikethrough" not in classes and "strikethrough" not in parent_classes:
                                price = await span.inner_text(timeout=3000)
                                price = price.strip()
                                break
                    except:
                        pass

                    # Filtrar por marca
                    nombre_producto = name.lower()
                    marca_buscada = marca.lower()
                    
                    should_include = False
                    if marca_buscada in nombre_producto:
                        should_include = True
                    elif marca_buscada == "felices las vacas" and "jogurtti" in nombre_producto:
                        should_include = True
                    
                    if should_include and name not in seen_product_names:
                        seen_product_names.add(name)
                        all_products.append((name, price))
                        products_processed += 1
                        
                except Exception as e:
                    continue

            # Pausa entre páginas
            await asyncio.sleep(2)
            current_page += 1

        await browser.close()
        return [{"nombre": name, "precio": price} for name, price in all_products]

if __name__ == "__main__":
    marca = "not"
    resultados = asyncio.run(scrape_carrefour_marca(marca))
    print(f"\n🔎 Se encontraron {len(resultados)} productos para '{marca}':")
    
    for i, prod in enumerate(resultados, 1):
        print(f"{i:2d}. {prod['nombre']}")
        print(f"    💰 {prod['precio']}")
        print("-" * 40)