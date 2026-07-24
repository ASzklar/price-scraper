'use client'

import { useState } from 'react'
import ProductTable from './marca/[slug]/ProductTable'

type Marca = 'not' | 'vegetalex' | 'felices_las_vacas'
type Producto = { id: number; nombre: string }
type PrecioMap = Record<number, Record<string, number>>

interface BrandData {
  slug: Marca
  label: string
  productos: Producto[]
  precioMap: PrecioMap
}

interface Props {
  brands: BrandData[]
  supermercados: string[]
}

export default function HomeTabsClient({ brands, supermercados }: Props) {
  const [active, setActive] = useState<Marca>(brands[0]?.slug ?? 'not')
  const current = brands.find(b => b.slug === active)!

  return (
    <div>
      <div className="flex gap-2 mb-6 flex-wrap">
        {brands.map(b => (
          <button
            key={b.slug}
            onClick={() => setActive(b.slug)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors border ${
              active === b.slug
                ? 'bg-green-600 text-white border-green-600'
                : 'bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:border-green-400 dark:hover:border-green-600 hover:text-green-700 dark:hover:text-green-400'
            }`}
          >
            {b.label}
          </button>
        ))}
      </div>

      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        {current.productos.length} productos · precios más recientes
      </p>

      <ProductTable
        slug={active}
        productos={current.productos}
        precioMap={current.precioMap}
        supermercados={supermercados}
      />
    </div>
  )
}
