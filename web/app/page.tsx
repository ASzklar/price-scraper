import Link from 'next/link'
import { getDateRange } from '@/lib/queries'

export const revalidate = 3600 // refresca cada hora

export default async function Home() {
  const { min, max } = await getDateRange()

  const marcas = [
    { slug: 'not', label: 'NotCo', desc: 'Hamburguesas, milanesas, nuggets, helados y más', emoji: '🍔' },
    { slug: 'vegetalex', label: 'Vegetalex', desc: 'Medallones, milanesas y hot dogs vegetales', emoji: '🥗' },
    { slug: 'felices_las_vacas', label: 'Felices Las Vacas', desc: 'Quesos, yogures, alfajores y untables veganos', emoji: '🐮' },
  ]

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Comparador de precios veganos
        </h1>
        <p className="text-gray-500">
          Seguimiento diario en Carrefour, Coto, Día, Disco, La Anónima Cooperativa y Vea.
          {min && max && (
            <span className="ml-2 text-sm text-green-700 font-medium">
              Datos desde {min} hasta {max}
            </span>
          )}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {marcas.map((m) => (
          <Link
            key={m.slug}
            href={`/marca/${m.slug}`}
            className="bg-white rounded-xl border border-gray-200 p-6 hover:border-green-400 hover:shadow-md transition-all"
          >
            <div className="text-4xl mb-3">{m.emoji}</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-1">{m.label}</h2>
            <p className="text-sm text-gray-500">{m.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
