// app/reports/page.tsx

import { Button } from "@/components/ui/button"
import Link from "next/link"

export default function Reportes() {
  return (
    <main className="container mx-auto px-4 py-20 space-y-12 text-center max-w-3xl">
      <h1 className="text-4xl font-extrabold">📊 Reportes Premium</h1>
      <p className="text-lg text-muted-foreground leading-relaxed">
        Próximamente vas a poder acceder a reportes avanzados para encontrar oportunidades únicas, 
        seguir tendencias del mercado, detectar productos ideales para revender y mucho más.
      </p>

      <ul className="text-left text-base text-muted-foreground list-disc list-inside space-y-2">
        <li>Top descuentos históricos y bajadas de precio</li>
        <li>Oportunidades de arbitraje entre retailers</li>
        <li>Tendencias por categoría y análisis de comportamiento de precios</li>
        <li>Alertas personalizadas para revendedores</li>
        <li>Comparativas avanzadas entre productos similares</li>
        <li>Y muchas funcionalidades más...</li>
      </ul>

      <p className="text-base mt-4">
        Si querés enterarte cuando estén disponibles, seguinos en{" "}
        <Link href="https://twitter.com/TuPrecioIdealAr" target="_blank" className="underline">
          @TuPrecioIdealAr
        </Link>.
      </p>

      <Button asChild size="lg" className="mt-6">
        <Link href="/search">Volver al buscador</Link>
      </Button>
    </main>
  )
}
