"""
Módulo de acceso a Supabase para Price Scraper.
Provee funciones de upsert para dimensiones y hechos.
"""
import os
from datetime import date
from supabase import create_client, Client

_client: Client | None = None

SUPERMERCADOS = ['carrefour', 'coope', 'coto', 'dia', 'disco', 'vea']

MARCA_MAP = {
    'not': 'not',
    'vegetalex': 'vegetalex',
    'felices_las_vacas': 'felices_las_vacas',
    'Not': 'not',
    'Vegetalex': 'vegetalex',
    'Felices Las Vacas': 'felices_las_vacas',
}


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ['SUPABASE_URL']
        key = os.environ['SUPABASE_KEY']
        _client = create_client(url, key)
    return _client


def _upsert_fecha(fecha: date) -> int:
    """Inserta o recupera el id de una fecha en dim_fecha."""
    client = get_client()
    row = {
        'fecha': fecha.isoformat(),
        'anio': fecha.year,
        'mes': fecha.month,
        'dia': fecha.day,
        'dia_semana': fecha.weekday(),
    }
    res = (
        client.table('dim_fecha')
        .upsert(row, on_conflict='fecha')
        .execute()
    )
    return res.data[0]['id']


def _upsert_producto(nombre: str, marca: str) -> int:
    """Inserta o recupera el id de un producto en dim_producto."""
    client = get_client()
    marca_norm = MARCA_MAP.get(marca, marca)
    res = (
        client.table('dim_producto')
        .upsert({'nombre': nombre, 'marca': marca_norm}, on_conflict='nombre')
        .execute()
    )
    return res.data[0]['id']


def _get_supermercado_ids() -> dict[str, int]:
    """Devuelve un dict {nombre: id} para todos los supermercados."""
    client = get_client()
    res = client.table('dim_supermercado').select('id, nombre').execute()
    return {row['nombre']: row['id'] for row in res.data}


def insert_precios(fecha: date, marca: str, filas: list[dict]) -> None:
    """
    Inserta precios en fact_precios.

    filas: lista de dicts con claves:
        producto_unificado (str), carrefour, coope, coto, dia, disco, vea (float|None)
    """
    client = get_client()
    fecha_id = _upsert_fecha(fecha)
    super_ids = _get_supermercado_ids()

    records = []
    for fila in filas:
        producto_id = _upsert_producto(fila['producto_unificado'], marca)
        for super_nombre in SUPERMERCADOS:
            precio = fila.get(super_nombre)
            if precio is None:
                continue
            try:
                precio_float = float(precio)
            except (TypeError, ValueError):
                continue
            records.append({
                'fecha_id': fecha_id,
                'producto_id': producto_id,
                'supermercado_id': super_ids[super_nombre],
                'precio': precio_float,
            })

    if not records:
        return

    # Insertar en lotes de 500
    for i in range(0, len(records), 500):
        client.table('fact_precios').upsert(
            records[i:i + 500],
            on_conflict='fecha_id,producto_id,supermercado_id'
        ).execute()

    print(f'[DB] Insertados {len(records)} registros para {marca} - {fecha.isoformat()}')
