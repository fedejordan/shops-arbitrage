import type React from "react"
import type { Metadata } from "next"
import Script from "next/script";
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
      <head>
        {/* Google Analytics */}
        <Script
          strategy="afterInteractive"
          src={`https://www.googletagmanager.com/gtag/js?id=G-3DQX8E6ME0`} // Reemplazá con tu ID
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-3DQX8E6ME0');
          `}
        </Script>
      </head>
      <body className={inter.className}>
        <Header />
        {children}
      </body>
    </html>
  )
}



import './globals.css'