'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { supabase } from '@/lib/supabase'
import { MARCA_LABELS, type Marca } from '@/lib/queries'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const SUPER_COLORS: Record<string, string> = {
  carrefour: '#2563eb',
  coope: '#7c3aed',
  coto: '#dc2626',
  dia: '#d97706',
  disco: '#059669',
  vea: '#0891b2',
}

function formatPrecio(v: number) {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(v)
}

export default function ProductoPage() {
  const params = useParams()
  const slug = params.slug as string
  const productoId = Number(params.id)

  const [nombre, setNombre] = useState('')
  const [chartData, setChartData] = useState<any[]>([])
  const [supermercados, setSupermercados] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      // Nombre del producto
      const { data: prod } = await supabase
        .from('dim_producto')
        .select('nombre')
        .eq('id', productoId)
        .single()
      if (prod) setNombre(prod.nombre)

      // Precios históricos
      const { data: rows } = await supabase
        .from('fact_precios')
        .select('precio, dim_fecha!inner(fecha), dim_supermercado!inner(nombre)')
        .eq('producto_id', productoId)
        .order('dim_fecha(fecha)', { ascending: true })

      if (!rows) { setLoading(false); return }

      // Pivotear: fecha -> { supermercado: precio }
      const byFecha: Record<string, Record<string, number>> = {}
      const superSet = new Set<string>()
      for (const row of rows) {
        const fecha = (row.dim_fecha as any).fecha
        const super_ = (row.dim_supermercado as any).nombre
        superSet.add(super_)
        if (!byFecha[fecha]) byFecha[fecha] = {}
        byFecha[fecha][super_] = row.precio
      }

      const sorted = Object.entries(byFecha)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([fecha, precios]) => ({ fecha, ...precios }))

      setChartData(sorted)
      setSupermercados([...superSet].sort())
      setLoading(false)
    }
    load()
  }, [productoId])

  const marca = slug as Marca

  return (
    <div>
      <div className="mb-6">
        <Link href={`/marca/${slug}`} className="text-sm text-gray-400 hover:text-green-700">
          ← {MARCA_LABELS[marca]}
        </Link>
        <h1 className="text-xl font-bold mt-1">{nombre || '...'}</h1>
        <p className="text-sm text-gray-500">Evolución de precios por supermercado</p>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400">Cargando...</div>
      ) : chartData.length === 0 ? (
        <div className="text-center py-16 text-gray-400">Sin datos disponibles</div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
            <ResponsiveContainer width="100%" height={340}>
              <LineChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="fecha"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => v.slice(5)} // MM-DD
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                  width={48}
                />
                <Tooltip
                  formatter={(v: number) => formatPrecio(v)}
                  labelFormatter={(l) => `Fecha: ${l}`}
                />
                <Legend />
                {supermercados.map(s => (
                  <Line
                    key={s}
                    type="monotone"
                    dataKey={s}
                    stroke={SUPER_COLORS[s] ?? '#888'}
                    dot={false}
                    strokeWidth={2}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Último precio por supermercado */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {supermercados.map(s => {
              const ultimoValor = [...chartData].reverse().find(d => d[s] != null)?.[s]
              return (
                <div key={s} className="bg-white rounded-xl border border-gray-200 p-4">
                  <div className="text-xs text-gray-400 capitalize mb-1">{s}</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {ultimoValor ? formatPrecio(ultimoValor) : '—'}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
