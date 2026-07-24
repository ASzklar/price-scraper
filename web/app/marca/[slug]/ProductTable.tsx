'use client'

import { useState } from 'react'
import Link from 'next/link'

const SUPER_RENAMES: Record<string, string> = {
  carrefour: 'Carrefour',
  coope: 'Cooperativa Obrera',
  coto: 'Coto',
  dia: 'Dia',
  disco: 'Disco',
  vea: 'Vea',
}

function formatPrecio(precio: number) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(precio)
}

type Producto = { id: number; nombre: string }
type PrecioMap = Record<number, Record<string, number>>

interface Props {
  slug: string
  productos: Producto[]
  precioMap: PrecioMap
  supermercados: string[]
  historicalAvg?: Record<number, number>
}

export default function ProductTable({ slug, productos, precioMap, supermercados, historicalAvg }: Props) {
  const [query, setQuery] = useState('')

  const filtered = query.trim()
    ? productos.filter(p => p.nombre.toLowerCase().includes(query.toLowerCase()))
    : productos

  return (
    <div>
      <div className="mb-4">
        <input
          type="search"
          placeholder="Filtrar por producto..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          className="w-full sm:w-80 px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        />
      </div>

      <div className="overflow-x-auto overflow-y-auto max-h-80 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <table className="w-full text-xs">
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800">
              <th className="text-left px-4 py-1.5 font-medium text-gray-600 dark:text-gray-300 min-w-[200px]">Producto</th>
              {supermercados.map(s => (
                <th key={s} className="text-right px-3 py-1.5 font-medium text-gray-600 dark:text-gray-300">
                  {SUPER_RENAMES[s] ?? s}
                </th>
              ))}
              {historicalAvg && (
                <th className="text-right px-3 py-1.5 font-medium text-gray-500 dark:text-gray-400 border-l border-gray-100 dark:border-gray-800">
                  Promedio histórico
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={supermercados.length + 1 + (historicalAvg ? 1 : 0)} className="text-center px-4 py-8 text-gray-400">
                  No se encontraron productos
                </td>
              </tr>
            ) : filtered.map((prod, i) => {
              const precios = precioMap[prod.id] ?? {}
              const valores = Object.values(precios).filter(Boolean)
              const minPrecio = valores.length ? Math.min(...valores) : null
              const maxPrecio = valores.length > 1 ? Math.max(...valores) : null
              const avg = historicalAvg?.[prod.id]

              return (
                <tr
                  key={prod.id}
                  className={`border-b border-gray-50 dark:border-gray-800 hover:bg-green-50 dark:hover:bg-green-950/30 transition-colors ${i % 2 === 0 ? '' : 'bg-gray-50/40 dark:bg-gray-800/30'}`}
                >
                  <td className="px-4 py-1">
                    <Link href={`/marca/${slug}/producto/${prod.id}`} className="text-green-700 dark:text-green-400 hover:underline font-medium">
                      {prod.nombre}
                    </Link>
                  </td>
                  {supermercados.map(s => {
                    const precio = precios[s]
                    const esMin = precio != null && minPrecio != null && precio === minPrecio
                    const esMax = precio != null && maxPrecio != null && precio === maxPrecio
                    return (
                      <td
                        key={s}
                        className={`px-3 py-1 text-right tabular-nums ${
                          esMin
                            ? 'bg-green-50 dark:bg-green-950/40 text-green-800 dark:text-green-300 font-semibold'
                            : esMax
                            ? 'bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-400 font-semibold'
                            : precio
                            ? 'text-gray-700 dark:text-gray-300'
                            : 'text-gray-300 dark:text-gray-600'
                        }`}
                      >
                        {precio ? formatPrecio(precio) : '—'}
                      </td>
                    )
                  })}
                  {historicalAvg && (
                    <td className="px-3 py-1 text-right tabular-nums text-gray-500 dark:text-gray-400 border-l border-gray-100 dark:border-gray-800">
                      {avg != null ? formatPrecio(avg) : '—'}
                    </td>
                  )}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
