'use client'

import { useState, useEffect } from 'react'
import ProductTable from './marca/[slug]/ProductTable'
import { getPrecioEvolucion } from '@/lib/queries'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import type { Oportunidad } from '@/lib/queries'

type Marca = 'not' | 'vegetalex' | 'felices_las_vacas'
type Producto = { id: number; nombre: string }
type PrecioMap = Record<number, Record<string, number>>

const SUPER_COLORS: Record<string, string> = {
  carrefour: '#2563eb',
  coope: '#7c3aed',
  coto: '#dc2626',
  dia: '#d97706',
  disco: '#059669',
  vea: '#db2777',
}

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

interface BrandData {
  slug: Marca
  label: string
  productos: Producto[]
  precioMap: PrecioMap
  historicalAvg: Record<number, number>
  oportunidades: Oportunidad[]
}

interface Props {
  brands: BrandData[]
  supermercados: string[]
}

// ---- 30-day evolution chart (client fetch) ----
function EvolucionChart({ productos }: { productos: Producto[] }) {
  const [selectedId, setSelectedId] = useState<number>(productos[0]?.id ?? 0)
  const [chartData, setChartData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!selectedId) return
    setLoading(true)
    getPrecioEvolucion(selectedId).then(rows => {
      // rows: { precio, dim_fecha: {fecha}, dim_supermercado: {nombre} }[]
      // Group by fecha, collect prices per supermarket
      const byDate: Record<string, Record<string, number>> = {}
      const cutoff = new Date()
      cutoff.setDate(cutoff.getDate() - 30)

      for (const row of rows) {
        const fecha = (row.dim_fecha as any).fecha as string
        if (new Date(fecha) < cutoff) continue
        const sup = (row.dim_supermercado as any).nombre as string
        if (!byDate[fecha]) byDate[fecha] = {}
        byDate[fecha][sup] = row.precio
      }

      const sorted = Object.entries(byDate)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([fecha, precios]) => ({ fecha, ...precios }))

      setChartData(sorted)
      setLoading(false)
    })
  }, [selectedId])

  const supermercados = Array.from(
    new Set(chartData.flatMap(d => Object.keys(d).filter(k => k !== 'fecha')))
  )

  return (
    <div>
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <label className="text-sm font-medium text-gray-600 dark:text-gray-300">Producto:</label>
        <select
          value={selectedId}
          onChange={e => setSelectedId(Number(e.target.value))}
          className="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        >
          {productos.map(p => (
            <option key={p.id} value={p.id}>{p.nombre}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="h-64 flex items-center justify-center text-gray-400 text-sm">Cargando datos...</div>
      ) : chartData.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-gray-400 text-sm">Sin datos para los últimos 30 días</div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="fecha"
              tick={{ fontSize: 11 }}
              tickFormatter={v => v.slice(5)} // MM-DD
            />
            <YAxis
              tick={{ fontSize: 11 }}
              tickFormatter={v => `$${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip
              formatter={(value: any) => formatPrecio(value)}
              labelFormatter={l => `Fecha: ${l}`}
            />
            <Legend formatter={v => SUPER_RENAMES[v] ?? v} />
            {supermercados.map(sup => (
              <Line
                key={sup}
                type="monotone"
                dataKey={sup}
                name={sup}
                stroke={SUPER_COLORS[sup] ?? '#6b7280'}
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

// ---- Oportunidades cards ----
function OportunidadesSection({ oportunidades }: { oportunidades: Oportunidad[] }) {
  if (oportunidades.length === 0) {
    return <p className="text-sm text-gray-400">No hay oportunidades disponibles hoy.</p>
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {oportunidades.map(op => (
        <div
          key={op.productoId}
          className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 flex flex-col gap-2"
        >
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 leading-tight">{op.nombre}</p>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100 tabular-nums">
            {formatPrecio(op.minPrecio)}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">{op.superMinimo}</p>
          <span className="inline-block self-start px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-400 text-xs font-semibold">
            -{op.ahorrosPct.toFixed(0)}% vs promedio
          </span>
        </div>
      ))}
    </div>
  )
}

// ---- Main component ----
export default function HomeTabsClient({ brands, supermercados }: Props) {
  const [active, setActive] = useState<Marca>(brands[0]?.slug ?? 'not')
  const current = brands.find(b => b.slug === active)!

  return (
    <div>
      {/* Brand tabs */}
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

      {/* Section 1 — Price table */}
      <section className="mb-10">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-1">Precios más recientes</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          {current.productos.length} productos · verde = mínimo, rojo = máximo por fila
        </p>
        <ProductTable
          slug={active}
          productos={current.productos}
          precioMap={current.precioMap}
          supermercados={supermercados}
          historicalAvg={current.historicalAvg}
        />
      </section>

      {/* Section 2 — 30-day evolution chart */}
      <section className="mb-10">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-1">Evolución de los últimos 30 días</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Precio por supermercado a lo largo del tiempo</p>
        <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
          <EvolucionChart key={active} productos={current.productos} />
        </div>
      </section>

      {/* Section 3 — Oportunidades de ahorro */}
      <section className="mb-4">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-1">Oportunidades de hoy</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Productos con mayor descuento vs. su promedio histórico
        </p>
        <OportunidadesSection oportunidades={current.oportunidades} />
      </section>
    </div>
  )
}
