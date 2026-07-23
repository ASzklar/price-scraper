import { notFound } from 'next/navigation'
import Link from 'next/link'
import { getProductosByMarca, getUltimosPrecios, MARCA_LABELS, type Marca } from '@/lib/queries'

export const revalidate = 3600

const MARCAS_VALIDAS: Marca[] = ['not', 'vegetalex', 'felices_las_vacas']

function formatPrecio(precio: number) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(precio)
}

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
        <Link href="/" className="text-sm text-gray-400 hover:text-green-700">← Inicio</Link>
        <h1 className="text-2xl font-bold mt-1">{MARCA_LABELS[marca]}</h1>
        <p className="text-sm text-gray-500">{productos.length} productos · precios más recientes</p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left px-4 py-3 font-medium text-gray-600 min-w-[200px]">Producto</th>
              {supermercados.map(s => (
                <th key={s} className="text-right px-3 py-3 font-medium text-gray-600 capitalize">{s}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {productos.map((prod, i) => {
              const precios = precioMap[prod.id] ?? {}
              const valores = Object.values(precios).filter(Boolean)
              const minPrecio = valores.length ? Math.min(...valores) : null

              return (
                <tr key={prod.id} className={`border-b border-gray-50 hover:bg-green-50 transition-colors ${i % 2 === 0 ? '' : 'bg-gray-50/40'}`}>
                  <td className="px-4 py-2.5">
                    <Link href={`/marca/${slug}/producto/${prod.id}`} className="text-green-700 hover:underline font-medium">
                      {prod.nombre}
                    </Link>
                  </td>
                  {supermercados.map(s => {
                    const precio = precios[s]
                    const esMenor = precio && minPrecio && precio === minPrecio
                    return (
                      <td key={s} className={`px-3 py-2.5 text-right tabular-nums ${esMenor ? 'text-green-700 font-semibold' : 'text-gray-700'} ${!precio ? 'text-gray-300' : ''}`}>
                        {precio ? formatPrecio(precio) : '—'}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
