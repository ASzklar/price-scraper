"""Re-sube los 3 CSVs que fallaron por ConnectionTerminated."""
import os
import re
from datetime import date
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from db import insert_precios

CLEANED = os.path.join("Data", "Cleaned")
FAILED = [
    "productos_felices_las_vacas_unificados_2026-05-18.csv",
    "productos_not_unificados_2026-01-28.csv",
    "productos_vegetalex_unificados_2026-03-03.csv",
]

for filename in FAILED:
    path = os.path.join(CLEANED, filename)
    if not os.path.exists(path):
        print(f"[MISSING] {filename}")
        continue
    m = re.match(r'productos_(\w+)_unificados_(\d{4}-\d{2}-\d{2})\.csv', filename)
    marca, fecha_str = m.group(1), m.group(2)
    df = pd.read_csv(path, encoding='utf-8')
    if df.empty:
        print(f"[SKIP] Vacío: {filename}")
        continue
    filas = df.to_dict('records')
    try:
        insert_precios(date.fromisoformat(fecha_str), marca, filas)
        print(f"[OK] {filename}")
    except Exception as e:
        print(f"[ERROR] {filename}: {e}")
