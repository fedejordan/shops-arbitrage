"use client"

import { SearchForm } from "@/components/search-form"
import { Button } from "@/components/ui/button"
import Link from "next/link"


export default function HomeSearch() {
  return (
    <section id="buscador" className="max-w-5xl mx-auto pt-10 border-t">
      <h2 className="text-2xl font-semibold mb-4 text-center">Probá el buscador</h2>
      <div className="max-w-3xl mx-auto">
      <Button asChild size="lg">
        <Link href="/search">Ir al buscador</Link>
      </Button>
      </div>
    </section>
  )
}
