import { supabase } from './supabase'

export type Marca = 'not' | 'vegetalex' | 'felices_las_vacas'

export const MARCA_LABELS: Record<Marca, string> = {
  not: 'NotCo',
  vegetalex: 'Vegetalex',
  felices_las_vacas: 'Felices Las Vacas',
}

export const SUPERMERCADOS = ['carrefour', 'coope', 'coto', 'dia', 'disco', 'vea']

/** Rango de fechas disponibles en la DB */
export async function getDateRange() {
  const { data } = await supabase
    .from('dim_fecha')
    .select('fecha')
    .order('fecha', { ascending: true })
  if (!data || data.length === 0) return { min: null, max: null }
  return { min: data[0].fecha as string, max: data[data.length - 1].fecha as string }
}

/** Todos los productos de una marca */
export async function getProductosByMarca(marca: Marca) {
  const { data } = await supabase
    .from('dim_producto')
    .select('id, nombre')
    .eq('marca', marca)
    .order('nombre')
  return data ?? []
}

/** Evolución de precio de un producto en todos los supermercados */
export async function getPrecioEvolucion(productoId: number) {
  const { data } = await supabase
    .from('fact_precios')
    .select(`
      precio,
      dim_fecha!inner(fecha),
      dim_supermercado!inner(nombre)
    `)
    .eq('producto_id', productoId)
    .order('dim_fecha(fecha)', { ascending: true })
  return data ?? []
}

/** Precio más reciente de todos los productos de una marca, por supermercado */
export async function getUltimosPrecios(marca: Marca) {
  // Step 1: product ids for this brand
  const { data: prods } = await supabase
    .from('dim_producto')
    .select('id')
    .eq('marca', marca)
  if (!prods || prods.length === 0) return []
  const ids = prods.map((p: any) => p.id)

  // Step 2: latest fecha_id that has data for these products
  const { data: fechaData } = await supabase
    .from('fact_precios')
    .select('fecha_id')
    .in('producto_id', ids)
    .order('fecha_id', { ascending: false })
    .limit(1)
  if (!fechaData || fechaData.length === 0) return []
  const ultimaFechaId = fechaData[0].fecha_id

  // Step 3: all prices for those products on that fecha_id
  const { data } = await supabase
    .from('fact_precios')
    .select('precio, dim_producto!inner(id, nombre, marca), dim_supermercado!inner(nombre), dim_fecha!inner(fecha)')
    .in('producto_id', ids)
    .eq('fecha_id', ultimaFechaId)
  return data ?? []
}

/** Promedio histórico de precio por producto para una marca. Returns Record<productoId, avgPrecio> */
export async function getHistoricalAvg(marca: Marca): Promise<Record<number, number>> {
  const { data: prods } = await supabase
    .from('dim_producto')
    .select('id')
    .eq('marca', marca)
  if (!prods || prods.length === 0) return {}
  const ids = prods.map((p: any) => p.id)

  const { data } = await supabase
    .from('fact_precios')
    .select('producto_id, precio')
    .in('producto_id', ids)
  if (!data) return {}

  const sums: Record<number, { sum: number; count: number }> = {}
  for (const row of data) {
    const pid = row.producto_id as number
    if (!sums[pid]) sums[pid] = { sum: 0, count: 0 }
    sums[pid].sum += row.precio
    sums[pid].count += 1
  }
  const result: Record<number, number> = {}
  for (const [pid, { sum, count }] of Object.entries(sums)) {
    result[Number(pid)] = sum / count
  }
  return result
}

export interface Oportunidad {
  productoId: number
  nombre: string
  minPrecio: number
  superMinimo: string
  ahorrosPct: number
}

/** Top 5 oportunidades de ahorro: productos con mayor descuento vs promedio histórico */
export async function getOportunidades(marca: Marca): Promise<Oportunidad[]> {
  const [productos, ultimos, historicalAvg] = await Promise.all([
    getProductosByMarca(marca),
    getUltimosPrecios(marca),
    getHistoricalAvg(marca),
  ])

  // Build min price per product today
  const minMap: Record<number, { precio: number; super_: string }> = {}
  for (const row of ultimos) {
    const prod = row.dim_producto as any
    const sup = row.dim_supermercado as any
    const pid = prod.id as number
    if (!minMap[pid] || row.precio < minMap[pid].precio) {
      minMap[pid] = { precio: row.precio, super_: sup.nombre }
    }
  }

  const SUPER_RENAMES: Record<string, string> = {
    carrefour: 'Carrefour',
    coope: 'Cooperativa Obrera',
    coto: 'Coto',
    dia: 'Dia',
    disco: 'Disco',
    vea: 'Vea',
  }

  const oportunidades: Oportunidad[] = []
  for (const prod of productos) {
    const min = minMap[prod.id]
    const avg = historicalAvg[prod.id]
    if (!min || !avg || avg === 0) continue
    const ahorrosPct = ((avg - min.precio) / avg) * 100
    if (ahorrosPct <= 0) continue
    oportunidades.push({
      productoId: prod.id,
      nombre: prod.nombre,
      minPrecio: min.precio,
      superMinimo: SUPER_RENAMES[min.super_] ?? min.super_,
      ahorrosPct,
    })
  }

  return oportunidades.sort((a, b) => b.ahorrosPct - a.ahorrosPct).slice(0, 5)
}

/** Comparar precio de un producto en la última fecha disponible */
export async function getPrecioComparacion(productoId: number) {
  const { data } = await supabase
    .from('fact_precios')
    .select(`
      precio,
      dim_supermercado!inner(nombre),
      dim_fecha!inner(fecha)
    `)
    .eq('producto_id', productoId)
    .order('dim_fecha(fecha)', { ascending: false })

  // Agrupar por supermercado, quedarse con el último precio de cada uno
  const bySuper: Record<string, { precio: number; fecha: string }> = {}
  for (const row of data ?? []) {
    const super_nombre = (row.dim_supermercado as any).nombre
    if (!bySuper[super_nombre]) {
      bySuper[super_nombre] = {
        precio: row.precio,
        fecha: (row.dim_fecha as any).fecha,
      }
    }
  }
  return bySuper
}
