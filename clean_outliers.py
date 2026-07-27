"""
Detecta y elimina precios outlier de fact_precios.

Criterio: para cada (producto_id, fecha_id), si un precio supera 2x la mediana
de todos los precios de ese producto en esa fecha, se considera outlier.
Si un producto sólo tiene 1 precio en esa fecha, se compara contra la mediana
histórica del producto (últimos 90 días).

Modo DRY_RUN=True: solo muestra los outliers sin borrar nada.
"""
import os
import statistics
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

DRY_RUN = True  # Cambiar a False para borrar efectivamente

client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

print("Descargando fact_precios...")
res = client.table('fact_precios').select('id, producto_id, fecha_id, supermercado_id, precio').execute()
rows = res.data
print(f"  {len(rows)} filas descargadas")

# Indexar por (producto_id, fecha_id)
from collections import defaultdict
by_prod_fecha: dict[tuple, list] = defaultdict(list)
for r in rows:
    key = (r['producto_id'], r['fecha_id'])
    by_prod_fecha[key].append(r)

# Calcular mediana histórica por producto (para casos con 1 solo precio en la fecha)
by_prod: dict[int, list] = defaultdict(list)
for r in rows:
    by_prod[r['producto_id']].append(r['precio'])

hist_median: dict[int, float] = {}
for pid, precios in by_prod.items():
    if len(precios) >= 2:
        hist_median[pid] = statistics.median(precios)

THRESHOLD = 2.0  # precio > 2x mediana → outlier

outlier_ids: list[int] = []

for (prod_id, fecha_id), group in by_prod_fecha.items():
    precios = [r['precio'] for r in group]

    if len(precios) >= 2:
        med = statistics.median(precios)
    elif prod_id in hist_median:
        med = hist_median[prod_id]
    else:
        continue  # no hay suficiente contexto

    for r in group:
        if r['precio'] > THRESHOLD * med:
            outlier_ids.append(r['id'])

# Obtener nombres para el reporte
prod_ids_needed = set()
for r in rows:
    if r['id'] in set(outlier_ids):
        prod_ids_needed.add(r['producto_id'])

# Mapas de nombres
prod_res = client.table('dim_producto').select('id, nombre').execute()
prod_map = {r['id']: r['nombre'] for r in prod_res.data}

super_res = client.table('dim_supermercado').select('id, nombre').execute()
super_map = {r['id']: r['nombre'] for r in super_res.data}

fecha_res = client.table('dim_fecha').select('id, fecha').execute()
fecha_map = {r['id']: r['fecha'] for r in fecha_res.data}

outlier_rows = [r for r in rows if r['id'] in set(outlier_ids)]
outlier_rows.sort(key=lambda r: (prod_map.get(r['producto_id'], ''), r['fecha_id']))

print(f"\n{'='*70}")
print(f"OUTLIERS DETECTADOS: {len(outlier_rows)}")
print(f"{'='*70}")
for r in outlier_rows:
    prod_name = prod_map.get(r['producto_id'], f"id={r['producto_id']}")
    super_name = super_map.get(r['supermercado_id'], f"id={r['supermercado_id']}")
    fecha = fecha_map.get(r['fecha_id'], f"id={r['fecha_id']}")
    # Calcular mediana del grupo para mostrar
    group = by_prod_fecha[(r['producto_id'], r['fecha_id'])]
    precios_grupo = [x['precio'] for x in group]
    if len(precios_grupo) >= 2:
        med = statistics.median(precios_grupo)
    else:
        med = hist_median.get(r['producto_id'], 0)
    print(f"  [{r['id']}] {prod_name[:45]:<45} | {super_name:<12} | {fecha} | ${r['precio']:>10,.0f}  (mediana: ${med:>8,.0f})")

if not outlier_ids:
    print("No se encontraron outliers.")
elif DRY_RUN:
    print(f"\n[DRY RUN] No se borró nada. Para eliminar, cambiar DRY_RUN = False y volver a ejecutar.")
else:
    print(f"\nEliminando {len(outlier_ids)} filas...")
    # Borrar en lotes de 100
    BATCH = 100
    deleted = 0
    for i in range(0, len(outlier_ids), BATCH):
        batch = outlier_ids[i:i+BATCH]
        client.table('fact_precios').delete().in_('id', batch).execute()
        deleted += len(batch)
        print(f"  Eliminadas {deleted}/{len(outlier_ids)}")
    print(f"Listo. {deleted} filas eliminadas.")
