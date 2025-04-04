"use client"

import type React from "react"
import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from "@/components/ui/select"
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

  // filtros (sin funcionalidad aún)
  const [retailer, setRetailer] = useState("")
  const [category, setCategory] = useState("")
  const [sortBy, setSortBy] = useState("")
  const [priceMin, setPriceMin] = useState("")
  const [priceMax, setPriceMax] = useState("")

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!searchQuery.trim()) return

    setLoading(true)
    setSearched(true)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/products?query=${encodeURIComponent(searchQuery)}`)
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
      <form onSubmit={handleSearch} className="flex flex-col gap-4">
        <div className="flex gap-2">
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
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger>
              <SelectValue placeholder="Ordenar por" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="name">Nombre</SelectItem>
              <SelectItem value="price">Precio</SelectItem>
              <SelectItem value="retailer">Retailer</SelectItem>
              <SelectItem value="date">Fecha de agregado</SelectItem>
            </SelectContent>
          </Select>

          <Select value={retailer} onValueChange={setRetailer}>
            <SelectTrigger>
              <SelectValue placeholder="Filtrar por retailer" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="fravega">Frávega</SelectItem>
              <SelectItem value="garbarino">Garbarino</SelectItem>
              <SelectItem value="musimundo">Musimundo</SelectItem>
              <SelectItem value="coto">Coto</SelectItem>
              <SelectItem value="jumbo">Jumbo</SelectItem>
            </SelectContent>
          </Select>

          <Select value={category} onValueChange={setCategory}>
            <SelectTrigger>
              <SelectValue placeholder="Filtrar por categoría" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="electro">Electrodomésticos</SelectItem>
              <SelectItem value="tecnologia">Tecnología</SelectItem>
              <SelectItem value="hogar">Hogar</SelectItem>
              <SelectItem value="muebles">Muebles</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-2 gap-4">
          <Input
            type="number"
            placeholder="Precio mínimo"
            value={priceMin}
            onChange={(e) => setPriceMin(e.target.value)}
          />
          <Input
            type="number"
            placeholder="Precio máximo"
            value={priceMax}
            onChange={(e) => setPriceMax(e.target.value)}
          />
        </div>
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
                {products.length > 0 ? (
                  <>
                    Resultados para "{searchQuery}"{" "}
                    <span className="text-muted-foreground text-base">({products.length})</span>
                  </>
                ) : (
                  `No se encontraron resultados para "${searchQuery}"`
                )}
              </h2>
              <ProductList products={products} />
            </>
          )}
        </div>
      )}
    </div>
  )
}
