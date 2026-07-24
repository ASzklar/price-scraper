import { notFound } from 'next/navigation'
import Link from 'next/link'
import { getProductosByMarca, getUltimosPrecios, MARCA_LABELS, type Marca } from '@/lib/queries'
import ProductTable from './ProductTable'

export const revalidate = 3600

const MARCAS_VALIDAS: Marca[] = ['not', 'vegetalex', 'felices_las_vacas']

export default async function MarcaPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params

  if (!MARCAS_VALIDAS.includes(slug as Marca)) notFound()
  const marca = slug as Marca

  const [productos, ultimos] = await Promise.all([
    getProductosByMarca(marca),
    getUltimosPrecios(marca),
  ])

  // Armar mapa: productoId -> { supermercado -> precio }
  type PrecioMap = Record<number, Record<string, number>>
  const precioMap: PrecioMap = {}
  for (const row of ultimos) {
    const prod = row.dim_producto as any
    const super_ = row.dim_supermercado as any
    if (!precioMap[prod.id]) precioMap[prod.id] = {}
    precioMap[prod.id][super_.nombre] = row.precio
  }

  const supermercados = ['carrefour', 'coope', 'coto', 'dia', 'disco', 'vea']

  return (
    <div>
      <div className="mb-6">
        <Link href="/" className="text-sm text-gray-400 hover:text-green-700 dark:hover:text-green-400">← Inicio</Link>
        <h1 className="text-2xl font-bold mt-1 text-gray-900 dark:text-gray-100">{MARCA_LABELS[marca]}</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">{productos.length} productos · precios más recientes</p>
      </div>

      <ProductTable
        slug={slug}
        productos={productos}
        precioMap={precioMap}
        supermercados={supermercados}
      />
    </div>
  )
}
