'use client'

import { useEffect } from 'react'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('[app/error]', error)
  }, [error])

  return (
    <div className="text-center py-16">
      <p className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
        Hubo un problema cargando los datos
      </p>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
        No pudimos traer la información desde la base de datos. Puede ser algo temporal.
      </p>
      <button
        onClick={() => reset()}
        className="px-4 py-2 rounded-xl bg-green-700 text-white text-sm font-semibold hover:bg-green-800"
      >
        Reintentar
      </button>
    </div>
  )
}
