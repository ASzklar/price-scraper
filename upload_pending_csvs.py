"""
Sube a Supabase los CSVs que están en Data/Cleaned/ pero no llegaron a la DB.
Lee directamente los Cleaned (ya unificados) en lugar de reprocesar desde Raw.
"""
import os
import re
from datetime import date
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from db import insert_precios

CLEANED_PATH = os.path.join("Data", "Cleaned")

files = sorted(f for f in os.listdir(CLEANED_PATH) if f.endswith(".csv"))
print(f"Archivos encontrados en Cleaned: {len(files)}\n")

for filename in files:
    match = re.match(r'productos_(\w+)_unificados_(\d{4}-\d{2}-\d{2})\.csv', filename)
    if not match:
        print(f"[SKIP] Nombre no reconocido: {filename}")
        continue

    marca_slug_raw = match.group(1)
    fecha_str = match.group(2)
    fecha = date.fromisoformat(fecha_str)

    marca_map = {'not': 'not', 'vegetalex': 'vegetalex', 'felices_las_vacas': 'felices_las_vacas'}
    marca_slug = marca_map.get(marca_slug_raw)
    if not marca_slug:
        print(f"[SKIP] Marca desconocida: {marca_slug_raw}")
        continue

    df = pd.read_csv(os.path.join(CLEANED_PATH, filename), encoding='utf-8')
    if df.empty:
        print(f"[SKIP] Vacío: {filename}")
        continue

    filas = df.rename(columns={'producto_unificado': 'producto_unificado'}).to_dict('records')
    try:
        insert_precios(fecha, marca_slug, filas)
        print(f"[OK] {filename} — {len(filas)} filas para {fecha}")
    except Exception as e:
        print(f"[ERROR] {filename}: {e}")
