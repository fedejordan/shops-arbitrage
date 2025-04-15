"use client"

import Link from "next/link"
import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Twitter } from "lucide-react"
import HomeSearch from "@/components/home-search"
import { event } from "@/lib/gtag"

export default function Home() {
  return (
    <main className="container mx-auto px-4 py-16 space-y-24">
      {/* Hero Section */}
      <section className="text-center space-y-6 max-w-3xl mx-auto">
        <h1 className="text-6xl font-extrabold tracking-tight leading-tight">
          TuPrecioIdeal
        </h1>
        <p className="text-xl text-muted-foreground leading-relaxed">
          Compará precios entre retailers como Frávega, Garbarino, Coto, Musimundo y más. 
          Descubrí el mejor precio en segundos con historial de precios, alertas y descuentos.
        </p>
        <div className="flex justify-center gap-4 flex-wrap pt-4">
          <Button
            asChild
            size="lg"
            className="px-6 py-3 text-base"
            onClick={() =>
              event({
                action: "click_landing_ir_buscador",
                category: "landing",
                label: "main button",
              })
            }
          >
            <Link href="/search">Probar el buscador</Link>
          </Button>

          <Button
            asChild
            variant="outline"
            size="lg"
            className="px-6 py-3 text-base"
            onClick={() =>
              event({
                action: "click_landing_twitter",
                category: "landing",
                label: "follow button on X",
              })
            }
          >
            <Link
              href="https://twitter.com/TuPrecioIdealAr"
              target="_blank"
              className="flex gap-2 items-center"
            >
              <Twitter className="w-5 h-5" />
              Seguir en X
            </Link>
          </Button>
        </div>
      </section>

      {/* Funcionalidades */}
      <section className="max-w-6xl mx-auto space-y-12">
        <h2 className="text-4xl font-bold text-center mb-4">¿Qué ofrece TuPrecioIdeal?</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {[
            {
              icon: "🔍",
              title: "Buscador inteligente",
              text: "Encontrá productos al instante en múltiples tiendas con filtros por precio, categoría y tienda.",
            },
            {
              icon: "📉",
              title: "Historial de precios",
              text: "Visualizá cómo varió el precio de cada producto en el tiempo antes de comprar.",
            },
            {
              icon: "🔔",
              title: "Alertas personalizadas",
              text: "Próximamente vas a poder recibir alertas cuando un producto baje de precio.",
            },
            {
              icon: "📊",
              title: "Reportes premium",
              text: "Accedé a análisis exclusivos de precios, oportunidades de reventa y descuentos ocultos.",
            },
            {
              icon: "📱",
              title: "App mobile (en camino)",
              text: "Escaneá productos en tiendas físicas y descubrí si hay una mejor oferta online.",
            },
            {
              icon: "⚖️",
              title: "Comparador de productos",
              text: "Compará características y precios de productos similares para elegir mejor.",
            },
            {
              icon: "🚨",
              title: "Alertas para revendedores",
              text: "Detectá oportunidades de reventa cuando un producto baja fuerte en una tienda.",
            },
            {
              icon: "📈",
              title: "Tendencias del mercado",
              text: "Observá qué productos están subiendo o bajando más según el comportamiento histórico.",
            },
          ].map((item) => (
            <div
              key={item.title}
              className="bg-muted p-6 rounded-lg shadow-sm text-center space-y-2"
            >
              <div className="text-3xl">{item.icon}</div>
              <h3 className="text-xl font-semibold">{item.title}</h3>
              <p className="text-muted-foreground text-sm">{item.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Call to Action */}
      <section className="bg-primary text-primary-foreground rounded-xl py-12 px-6 text-center space-y-6 max-w-3xl mx-auto shadow-md">
        <h2 className="text-3xl font-bold">¿Listo para ahorrar?</h2>
        <p className="text-base opacity-90">
          Empezá ahora a comparar precios y descubrir las mejores ofertas del país.
        </p>
        <Button
          asChild
          size="lg"
          className="px-6 py-3 text-base"
          onClick={() =>
            event({
              action: "click_cta_save_money",
              category: "landing",
              label: "cta final button",
            })
          }
        >
          <Link href="/search">Ir al buscador</Link>
        </Button>
      </section>
    </main>
  )
}
