"use client"

import type React from "react"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ProductList } from "./product-list"
import type { Product } from "@/lib/types"
import { Search } from "lucide-react"

export function SearchForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const query = searchParams.get("q") || ""
  const [searchQuery, setSearchQuery] = useState(query)
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!searchQuery.trim()) return

    setLoading(true)
    setSearched(true)

    try {
      const response = await fetch(`http://127.0.0.1:8000/products?query=${encodeURIComponent(searchQuery)}`)
      const data = await response.json()
      setProducts(data)

      // Update URL with search query
      router.push(`/?q=${encodeURIComponent(searchQuery)}`, { scroll: false })
    } catch (error) {
      console.error("Error searching products:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSearch} className="flex gap-2">
        <Input
          type="text"
          placeholder="Buscar productos..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1"
        />
        <Button type="submit" disabled={loading}>
          {loading ? (
            <span className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
              Buscando
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Search className="h-4 w-4" />
              Buscar
            </span>
          )}
        </Button>
      </form>

      {searched && (
        <div>
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : (
            <>
              <h2 className="text-xl font-semibold mb-4">
                {products.length > 0
                  ? `Resultados para "${searchQuery}"`
                  : `No se encontraron resultados para "${searchQuery}"`}
              </h2>
              <ProductList products={products} />
            </>
          )}
        </div>
      )}
    </div>
  )
}

