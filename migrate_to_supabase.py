"""
Script de migración histórica: lee todos los CSVs de Data/Cleaned/
y los inserta en Supabase.

Uso:
    python migrate_to_supabase.py

Variables de entorno requeridas:
    SUPABASE_URL
    SUPABASE_KEY
"""
import os
import re
import pandas as pd
from datetime import date
from db import insert_precios

CLEANED_PATH = os.path.join('Data', 'Cleaned')

MARCA_SLUG_MAP = {
    'not': 'not',
    'vegetalex': 'vegetalex',
    'felices_las_vacas': 'felices_las_vacas',
}

# Nombre de columna en los CSVs de Cleaned
PRODUCTO_COL = 'producto_unificado'
SUPERMARKET_COLS = ['carrefour', 'coope', 'coto', 'dia', 'disco', 'vea']


def parse_price(val) -> float | None:
    if pd.isna(val):
        return None
    s = str(val).replace('$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(s)
    except ValueError:
        return None


def migrate_file(filepath: str) -> None:
    filename = os.path.basename(filepath)
    # productos_{marca}_unificados_{fecha}.csv
    match = re.match(r'productos_(.+?)_unificados_(\d{4}-\d{2}-\d{2})\.csv', filename)
    if not match:
        print(f'[SKIP] Formato no reconocido: {filename}')
        return

    marca_slug = match.group(1)
    fecha_str = match.group(2)

    if marca_slug not in MARCA_SLUG_MAP:
        print(f'[SKIP] Marca desconocida: {marca_slug}')
        return

    fecha = date.fromisoformat(fecha_str)
    df = pd.read_csv(filepath)

    if PRODUCTO_COL not in df.columns:
        print(f'[SKIP] Sin columna "{PRODUCTO_COL}": {filename}')
        return

    filas = []
    for _, row in df.iterrows():
        fila = {'producto_unificado': row[PRODUCTO_COL]}
        for col in SUPERMARKET_COLS:
            if col in row:
                fila[col] = parse_price(row[col])
        filas.append(fila)

    insert_precios(fecha, marca_slug, filas)


def main() -> None:
    if not os.path.isdir(CLEANED_PATH):
        print(f'[ERROR] No existe la carpeta: {CLEANED_PATH}')
        return

    archivos = sorted([
        f for f in os.listdir(CLEANED_PATH)
        if f.startswith('productos_') and f.endswith('.csv')
    ])

    if not archivos:
        print('[WARN] No se encontraron archivos en Data/Cleaned/')
        return

    print(f'[Migración] {len(archivos)} archivos a procesar...')

    for i, filename in enumerate(archivos, 1):
        filepath = os.path.join(CLEANED_PATH, filename)
        print(f'[{i}/{len(archivos)}] {filename}')
        try:
            migrate_file(filepath)
        except Exception as e:
            print(f'[ERROR] {filename}: {e}')

    print('[Migración] Completada.')


if __name__ == '__main__':
    main()
