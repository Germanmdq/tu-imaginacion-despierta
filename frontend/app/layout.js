import { Inter } from 'next/font/google'
import './globals.css'


export const metadata = {
  title: 'Tu Imaginación Despierta',
  description: 'Plataforma para controlar tu imaginación',
}

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
