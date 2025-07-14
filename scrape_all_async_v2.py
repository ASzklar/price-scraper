import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import time
import os

from scrape_carrefour_async import scrape_carrefour_marca
from scrape_coope_async import scrape_coope
from scrape_coto_async import scrape_coto_all_pages
from scrape_dia_async import scrape_dia
from scrape_disco_async import scrape_disco
from scrape_vea_async import scrape_vea_all_pages

async def scrape_otros_5(marca_a_buscar):
    """Ejecuta scraping en paralelo para 5 supermercados"""
    resultados = await asyncio.gather(
        scrape_coope(marca_a_buscar),
        scrape_coto_all_pages(marca_a_buscar),
        scrape_dia(marca_a_buscar),
        scrape_disco(marca_a_buscar),
        scrape_vea_all_pages(marca_a_buscar),
        return_exceptions=True
    )
    return resultados

async def scrape_all(marca_a_buscar):
    """Ejecuta scraping completo para una marca"""
    fecha = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 Iniciando scraping para: {marca_a_buscar}")
    
    # Scraper Carrefour
    try:
        carrefour = await scrape_carrefour_marca(marca_a_buscar)
        print(f"✅ Carrefour: {len(carrefour)} productos")
    except Exception as e:
        print(f"❌ Error Carrefour: {repr(e)}")
        carrefour = []
    
    await asyncio.sleep(3)
    
    # Otros scrapers en paralelo
    resultados_otros = await scrape_otros_5(marca_a_buscar)
    nombres_scrapers = ["coope", "coto", "dia", "disco", "vea"]
    datos_otros = []
    
    for nombre_scraper, r in zip(nombres_scrapers, resultados_otros):
        if isinstance(r, Exception):
            print(f"❌ Error {nombre_scraper}: {repr(r)}")
            datos_otros.append([])
        elif r is None:
            datos_otros.append([])
        else:
            print(f"✅ {nombre_scraper}: {len(r)} productos")
            datos_otros.append(r)
    
    coope, coto, dia, disco, vea = datos_otros
    
    # Compilar todos los datos
    datos = [carrefour, coope, coto, dia, disco, vea]
    
    # Verificar que tenemos productos
    total_productos = sum(len(d) for d in datos)
    if total_productos == 0:
        print(f"⚠️ No se encontraron productos para '{marca_a_buscar}'")
        return
    
    # Obtener nombres únicos de productos
    nombres_unicos = sorted(set(p['nombre'] for r in datos for p in r))
    print(f"📊 Total productos únicos: {len(nombres_unicos)}")
    
    # Crear DataFrame
    filas = []
    for nombre_producto in nombres_unicos:
        fila = {
            "fecha": fecha,
            "producto": nombre_producto,
            "carrefour": obtener_precio(carrefour, nombre_producto),
            "coope": obtener_precio(coope, nombre_producto),
            "coto": obtener_precio(coto, nombre_producto),
            "dia": obtener_precio(dia, nombre_producto),
            "disco": obtener_precio(disco, nombre_producto),
            "vea": obtener_precio(vea, nombre_producto),
        }
        filas.append(fila)
    
    df_precios = pd.DataFrame(filas)
    
    # Crear directorio Data/Raw si no existe
    data_raw_path = os.path.join("Data", "Raw")
    os.makedirs(data_raw_path, exist_ok=True)
    
    # Generar nombre de archivo y ruta completa
    marca_para_nombre_archivo = marca_a_buscar.replace(" ", "_").lower()
    nombre_archivo = f"precios_async_{fecha}_{marca_para_nombre_archivo}.csv"
    ruta_completa = os.path.join(data_raw_path, nombre_archivo)
    
    # Guardar archivo
    df_precios.to_csv(ruta_completa, index=False, encoding="utf-8")
    
    print(f"📦 Archivo guardado: {ruta_completa}")
    
    # Resumen por supermercado
    supermercados = ["carrefour", "coope", "coto", "dia", "disco", "vea"]
    for super in supermercados:
        productos_con_precio = df_precios[super].notna().sum()
        print(f"   {super.capitalize():12}: {productos_con_precio:2d} productos")

def obtener_precio(lista_productos_supermercado, nombre_producto_buscado):
    """Busca el precio de un producto en la lista de un supermercado"""
    for producto in lista_productos_supermercado:
        if producto["nombre"] == nombre_producto_buscado:
            return producto["precio"]
    return np.nan

async def main():
    """Función principal que maneja la ejecución secuencial de las marcas"""
    marcas_a_scrapear = ["Not", "Vegetalex", "Felices Las Vacas"]
    
    if len(sys.argv) > 1:
        marcas_a_scrapear = [" ".join(sys.argv[1:])]
    
    print(f"🎯 Scraping marcas: {', '.join(marcas_a_scrapear)}")
    
    inicio_total = time.time()
    
    for i, marca in enumerate(marcas_a_scrapear, 1):
        print(f"\n{'='*50}")
        print(f"🔍 MARCA {i}/{len(marcas_a_scrapear)}: {marca}")
        print(f"{'='*50}")
        
        inicio_marca = time.time()
        
        try:
            await scrape_all(marca)
            fin_marca = time.time()
            tiempo_marca = fin_marca - inicio_marca
            print(f"⏱️ Tiempo {marca}: {tiempo_marca:.1f}s")
            
            if i < len(marcas_a_scrapear):
                await asyncio.sleep(5)
                
        except Exception as e:
            print(f"❌ Error procesando '{marca}': {repr(e)}")
            continue
    
    fin_total = time.time()
    tiempo_total = fin_total - inicio_total
    print(f"\n🏁 PROCESO TERMINADO")
    print(f"⏱️ Tiempo total: {tiempo_total:.1f}s ({tiempo_total/60:.1f}min)")

if __name__ == "__main__":
    asyncio.run(main())