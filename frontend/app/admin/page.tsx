"use client"

import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"


type Stats = {
  total_products: number
  uncategorized_products: number
  products_with_history: number
  products_with_searchable_term: number
  products_with_ai_description: number
  total_retailers: number
  total_categories: number
  unmapped_retailer_categories: number
  invalid_price_products: number
}

export default function AdminHome() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  const url = process.env.NEXT_PUBLIC_API_BASE_URL

  useEffect(() => {
    fetch(`${url}/admin/stats`)
      .then(res => res.json())
      .then(data => {
        setStats(data)
        setLoading(false)
      })
  }, [])

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Panel de Administración</h1>
      <p className="text-muted-foreground text-sm">
        Bienvenido al panel. Desde aquí podés gestionar las categorías, productos y sugerencias automáticas.
      </p>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="p-4 border rounded-lg bg-white shadow-sm space-y-2">
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-8 w-1/3" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <StatCard label="🧾 Productos totales" value={stats!.total_products} />
          <StatCard label="🚫 Sin categoría" value={stats!.uncategorized_products} />
          <StatCard label="📊 Con historial de precios" value={stats!.products_with_history} />
          <StatCard label="🔍 Con searchable_term" value={stats!.products_with_searchable_term} />
          <StatCard label="🤖 Con ai_description" value={stats!.products_with_ai_description} />
          <StatCard label="🏪 Retailers" value={stats!.total_retailers} />
          <StatCard label="📂 Categorías" value={stats!.total_categories} />
          <StatCard label="❓ Categorías retailer sin mapear" value={stats!.unmapped_retailer_categories} />
          <StatCard label="⚠️ Precio inválido" value={stats!.invalid_price_products} />
        </div>
      )}


      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
        <AdminLink href="/admin/categories" title="Retailer Categories" description="Asignar categorías propias a categorías de retailers." />
        <AdminLink href="/admin/products" title="Productos sin Categoría" description="Categorizar productos que no fueron asignados automáticamente." />
        <AdminLink href="/admin/tweets" title="Sugerencias de Tweets" description="Generar contenido basado en datos de productos y precios." />
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="p-4 border rounded-lg bg-white shadow-sm">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-bold">{value.toLocaleString()}</p>
    </div>
  )
}

function AdminLink({ href, title, description }: { href: string, title: string, description: string }) {
  return (
    <a href={href} className="p-4 border rounded-lg hover:bg-gray-50 transition">
      <h2 className="font-semibold text-lg">{title}</h2>
      <p className="text-sm text-muted-foreground">{description}</p>
    </a>
  )
}
