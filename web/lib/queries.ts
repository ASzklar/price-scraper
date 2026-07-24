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
  // Step 1: get product ids for this brand
  const { data: prods } = await supabase
    .from('dim_producto')
    .select('id')
    .eq('marca', marca)
  if (!prods || prods.length === 0) return []
  const ids = prods.map(p => p.id)

  // Step 2: get the latest date that has data for any of these products
  const { data: fechaData } = await supabase
    .from('fact_precios')
    .select('dim_fecha!inner(fecha)')
    .in('producto_id', ids)
    .order('dim_fecha(fecha)', { ascending: false })
    .limit(1)
  if (!fechaData || fechaData.length === 0) return []
  const ultimaFecha = (fechaData[0].dim_fecha as any).fecha

  // Step 3: get all prices for those products on that date
  const { data } = await supabase
    .from('fact_precios')
    .select('precio, dim_producto!inner(id, nombre, marca), dim_supermercado!inner(nombre), dim_fecha!inner(fecha)')
    .in('producto_id', ids)
    .eq('dim_fecha.fecha', ultimaFecha)
  return data ?? []
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
