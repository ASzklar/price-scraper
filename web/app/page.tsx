import Link from 'next/link'
import { getDateRange } from '@/lib/queries'

export const revalidate = 3600 // refresca cada hora

export default async function Home() {
  const { min, max } = await getDateRange()

  // Format max date as DD/MM/YYYY for display
  function formatDate(d: string | null) {
    if (!d) return null
    const [y, m, day] = d.split('-')
    return `${day}/${m}/${y}`
  }

  const marcas = [
    { slug: 'not', label: 'NotCo', desc: 'Hamburguesas, milanesas, nuggets, helados y más', emoji: '🍔' },
    { slug: 'vegetalex', label: 'Vegetalex', desc: 'Medallones, milanesas y hot dogs vegetales', emoji: '🥗' },
    { slug: 'felices_las_vacas', label: 'Felices Las Vacas', desc: 'Quesos, yogures, alfajores y untables veganos', emoji: '🐮' },
  ]

  return (
    <div>
      <div className="mb-10">
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

      <div className="grid gap-5 sm:grid-cols-3">
        {marcas.map((m) => (
          <Link
            key={m.slug}
            href={`/marca/${m.slug}`}
            className="group relative bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 hover:border-green-400 dark:hover:border-green-600 hover:shadow-lg dark:hover:shadow-green-900/20 transition-all"
          >
            <div className="text-4xl mb-4">{m.emoji}</div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-1 group-hover:text-green-700 dark:group-hover:text-green-400 transition-colors">
              {m.label}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{m.desc}</p>
            {max && (
              <div className="text-xs text-gray-400 dark:text-gray-500 border-t border-gray-100 dark:border-gray-800 pt-3 mt-auto">
                Última actualización: <span className="font-medium text-gray-600 dark:text-gray-400">{formatDate(max)}</span>
              </div>
            )}
            <span className="absolute top-5 right-5 text-gray-300 dark:text-gray-600 group-hover:text-green-400 transition-colors text-lg">→</span>
          </Link>
        ))}
      </div>
    </div>
  )
}
