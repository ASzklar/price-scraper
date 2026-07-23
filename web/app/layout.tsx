import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Link from 'next/link'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Precios Veganos AR',
  description: 'Comparador de precios de productos veganos en supermercados argentinos',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className={`${inter.className} bg-gray-50 text-gray-900 min-h-screen`}>
        <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-6">
            <Link href="/" className="font-bold text-lg text-green-700 hover:text-green-800">
              🌱 Precios Veganos
            </Link>
            <nav className="flex gap-4 text-sm text-gray-600">
              <Link href="/marca/not" className="hover:text-green-700">NotCo</Link>
              <Link href="/marca/vegetalex" className="hover:text-green-700">Vegetalex</Link>
              <Link href="/marca/felices_las_vacas" className="hover:text-green-700">Felices Las Vacas</Link>
            </nav>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-6">
          {children}
        </main>
        <footer className="text-center text-xs text-gray-400 py-6 mt-8 border-t border-gray-100">
          Datos actualizados diariamente · NotCo · Vegetalex · Felices Las Vacas
        </footer>
      </body>
    </html>
  )
}
