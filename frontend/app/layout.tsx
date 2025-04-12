import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Header } from "@/components/header"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "TuPrecioIdeal - Compará precios entre tiendas y ahorrá más",
  description: "Buscador de productos en Frávega, Garbarino, Musimundo y más. Encontrá el mejor precio con alertas, historial y comparador inteligente.",
  generator: 'v0.dev',
}


export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <Header />
        {children}
      </body>
    </html>
  )
}



import './globals.css'