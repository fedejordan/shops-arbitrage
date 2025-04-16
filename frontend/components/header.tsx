"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Twitter } from "lucide-react"
import { event } from "@/lib/gtag"


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
          <Link
            href="/"
            onClick={() =>
              event({
                action: "click_nav_home",
                category: "navigation",
                label: "home",
              })
            }
          >
            Inicio
          </Link>
        </Button>
        <Button variant="ghost" asChild>
          <Link
            href="/search"
            onClick={() =>
              event({
                action: "click_nav_search",
                category: "navigation",
                label: "search",
              })
            }
          >
            Buscador
          </Link>
        </Button>

        <Button variant="ghost" asChild>
          <Link
            href="/reports"
            onClick={() =>
              event({
                action: "click_nav_reports",
                category: "navigation",
                label: "reports",
              })
            }
          >
            Reportes
          </Link>
        </Button>
        <Button variant="ghost" asChild>
          <Link
            href="https://twitter.com/TuPrecioIdealAr"
            target="_blank"
            onClick={() =>
              event({
                action: "click_nav_twitter",
                category: "navigation",
                label: "twitter",
              })
            }
          >
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
