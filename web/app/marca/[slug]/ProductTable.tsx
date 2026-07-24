'use client'

import { useState } from 'react'
import Link from 'next/link'

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
}

export default function ProductTable({ slug, productos, precioMap, supermercados }: Props) {
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

      <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800">
              <th className="text-left px-4 py-3 font-medium text-gray-600 dark:text-gray-300 min-w-[200px]">Producto</th>
              {supermercados.map(s => (
                <th key={s} className="text-right px-3 py-3 font-medium text-gray-600 dark:text-gray-300 capitalize">{s}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={supermercados.length + 1} className="text-center px-4 py-8 text-gray-400">
                  No se encontraron productos
                </td>
              </tr>
            ) : filtered.map((prod, i) => {
              const precios = precioMap[prod.id] ?? {}
              const valores = Object.values(precios).filter(Boolean)
              const minPrecio = valores.length ? Math.min(...valores) : null

              return (
                <tr
                  key={prod.id}
                  className={`border-b border-gray-50 dark:border-gray-800 hover:bg-green-50 dark:hover:bg-green-950/30 transition-colors ${i % 2 === 0 ? '' : 'bg-gray-50/40 dark:bg-gray-800/30'}`}
                >
                  <td className="px-4 py-2.5">
                    <Link href={`/marca/${slug}/producto/${prod.id}`} className="text-green-700 dark:text-green-400 hover:underline font-medium">
                      {prod.nombre}
                    </Link>
                  </td>
                  {supermercados.map(s => {
                    const precio = precios[s]
                    const esMenor = precio && minPrecio && precio === minPrecio
                    return (
                      <td
                        key={s}
                        className={`px-3 py-2.5 text-right tabular-nums ${esMenor ? 'text-green-700 dark:text-green-400 font-semibold' : 'text-gray-700 dark:text-gray-300'} ${!precio ? 'text-gray-300 dark:text-gray-600' : ''}`}
                      >
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
