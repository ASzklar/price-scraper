import { getDateRange, getProductosByMarca, getUltimosPrecios, getHistoricalAvg, computeOportunidades, MARCA_LABELS, type Marca } from '@/lib/queries'
import HomeTabsClient from './HomeTabsClient'

export const dynamic = 'force-dynamic'

const MARCAS: Marca[] = ['not', 'vegetalex', 'felices_las_vacas']
const SUPERMERCADOS = ['carrefour', 'coope', 'coto', 'dia', 'disco', 'vea']

function formatDate(d: string | null) {
  if (!d) return null
  const [y, m, day] = d.split('-')
  return `${day}/${m}/${y}`
}

export default async function Home() {
  const { min, max } = await getDateRange()

  const brandsRaw = await Promise.all(
    MARCAS.map(async (marca) => {
      const [productos, ultimos, historicalAvg] = await Promise.all([
        getProductosByMarca(marca),
        getUltimosPrecios(marca),
        getHistoricalAvg(marca),
      ])
      const oportunidades = computeOportunidades(productos, ultimos, historicalAvg)

      type PrecioMap = Record<number, Record<string, number>>
      const precioMap: PrecioMap = {}
      for (const row of ultimos) {
        const prod = row.dim_producto as any
        const super_ = row.dim_supermercado as any
        if (!precioMap[prod.id]) precioMap[prod.id] = {}
        precioMap[prod.id][super_.nombre] = row.precio
      }

      return { slug: marca, label: MARCA_LABELS[marca], productos, precioMap, historicalAvg, oportunidades }
    })
  )

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-50 mb-2">
          Comparador de precios veganos
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Seguimiento diario en Carrefour, Coto, Día, Disco, Cooperativa Obrera y Vea.
        </p>
        {min && max && (
          <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-50 dark:bg-green-950/40 border border-green-200 dark:border-green-800">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm text-green-700 dark:text-green-400 font-medium">
              Datos desde {formatDate(min)} hasta {formatDate(max)}
            </span>
          </div>
        )}
      </div>

      <HomeTabsClient brands={brandsRaw} supermercados={SUPERMERCADOS} />
    </div>
  )
}
