// components/header.tsx

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Twitter } from "lucide-react"

export function Header() {
  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        {/* Logo + Marca */}
        <Link href="/" className="font-bold text-xl tracking-tight">
          TuPrecioIdeal
        </Link>

        {/* Navegación */}
        <nav className="flex items-center gap-2">
          <Button variant="ghost" asChild>
            <Link href="/">Inicio</Link>
          </Button>
          <Button variant="ghost" asChild>
            <Link href="/search">Buscador</Link>
          </Button>
          <Button variant="ghost" asChild>
            <Link href="/reports">Reportes</Link>
          </Button>
          <Button variant="ghost" asChild>
            <Link href="https://twitter.com/TuPrecioIdealAr" target="_blank">
              <span className="flex items-center gap-1">
                <Twitter className="w-4 h-4" />
                X
              </span>
            </Link>
          </Button>
        </nav>
      </div>
    </header>
  )
}
