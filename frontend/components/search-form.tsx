"use client"

import type React from "react"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ProductList } from "./product-list"
import type { Product, ProductResponse } from "@/lib/types"
import { 
  Search, 
  SlidersHorizontal,
  ArrowUpDown,
  X 
} from "lucide-react"
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationPrevious,
  PaginationNext,
  PaginationEllipsis,
} from "@/components/ui/pagination"



export function SearchForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const query = searchParams.get("q") || ""
  const [searchQuery, setSearchQuery] = useState(query)
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  
  // Nuevos estados para filtros y ordenamiento
  const [showFilters, setShowFilters] = useState(false)
  const [sortBy, setSortBy] = useState("")
  const [priceRange, setPriceRange] = useState([0, 5000])
  const [selectedRetailers, setSelectedRetailers] = useState<string[]>([])
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])

  // Paginado
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const limit = 20 // o el número que prefieras

  
  // Datos de ejemplo para retailers y categorías
  const retailers = ["Amazon", "Mercado Libre", "Falabella", "Paris", "Ripley"]
  const categories = ["Electrónica", "Hogar", "Ropa", "Juguetes", "Deportes", "Mascotas"]

  const fetchProducts = async (pageToLoad: number) => {
    setLoading(true)
    setSearched(true)
  
    try {
      let url = `${process.env.NEXT_PUBLIC_API_BASE_URL}/products?query=${encodeURIComponent(searchQuery)}&page=${pageToLoad}&limit=${limit}`
  
      if (sortBy) url += `&sort=${sortBy}`
      if (selectedRetailers.length > 0) url += `&retailers=${selectedRetailers.join(',')}`
      if (selectedCategories.length > 0) url += `&categories=${selectedCategories.join(',')}`
      url += `&minPrice=${priceRange[0]}&maxPrice=${priceRange[1]}`
  
      const response = await fetch(url)
      const result: ProductResponse = await response.json()
      setProducts(result.data)
      setTotalPages(Math.ceil(result.total / limit))
      setPage(pageToLoad) // actualizás el estado recién después de éxito
  
      // Actualizar la URL
      let routerUrl = `/?q=${encodeURIComponent(searchQuery)}&page=${pageToLoad}`
      if (sortBy) routerUrl += `&sort=${sortBy}`
      if (selectedRetailers.length > 0) routerUrl += `&retailers=${selectedRetailers.join(',')}`
      if (selectedCategories.length > 0) routerUrl += `&categories=${selectedCategories.join(',')}`
      routerUrl += `&minPrice=${priceRange[0]}&maxPrice=${priceRange[1]}`
      router.push(routerUrl, { scroll: false })
    } catch (error) {
      console.error("Error searching products:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    fetchProducts(1) // siempre buscás desde la página 1 al hacer una nueva búsqueda
  }

  const toggleRetailer = (retailer: string) => {
    setSelectedRetailers(prev => 
      prev.includes(retailer) 
        ? prev.filter(r => r !== retailer)
        : [...prev, retailer]
    )
  }

  const toggleCategory = (category: string) => {
    setSelectedCategories(prev => 
      prev.includes(category) 
        ? prev.filter(c => c !== category)
        : [...prev, category]
    )
  }

  const handlePriceChange = (values: number[]) => {
    setPriceRange(values)
  }

  const clearFilters = () => {
    setSortBy("")
    setPriceRange([0, 5000])
    setSelectedRetailers([])
    setSelectedCategories([])
  }

  const activeFiltersCount = [
    sortBy !== "",
    selectedRetailers.length > 0,
    selectedCategories.length > 0,
    !(priceRange[0] === 0 && priceRange[1] === 5000)
  ].filter(Boolean).length

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4">
        <form onSubmit={handleSearch} className="flex gap-2">
          <Input
            type="text"
            placeholder="Buscar productos..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1"
          />
          <Popover open={showFilters} onOpenChange={setShowFilters}>
            <PopoverTrigger asChild>
              <Button 
                type="button" 
                variant="outline" 
                className="relative"
              >
                <SlidersHorizontal className="h-4 w-4" />
                {activeFiltersCount > 0 && (
                  <Badge 
                    className="absolute -top-2 -right-2 h-5 w-5 p-0 flex items-center justify-center"
                  >
                    {activeFiltersCount}
                  </Badge>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">Filtros y ordenamiento</h3>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={clearFilters}
                    className="h-8 text-xs"
                  >
                    Limpiar
                  </Button>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="sortBy">Ordenar por</Label>
                  <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger id="sortBy">
                      <SelectValue placeholder="Seleccionar orden" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="name_asc">Nombre (A-Z)</SelectItem>
                      <SelectItem value="name_desc">Nombre (Z-A)</SelectItem>
                      <SelectItem value="price_asc">Precio (menor a mayor)</SelectItem>
                      <SelectItem value="price_desc">Precio (mayor a menor)</SelectItem>
                      <SelectItem value="retailer_asc">Retailer (A-Z)</SelectItem>
                      <SelectItem value="date_desc">Más recientes primero</SelectItem>
                      <SelectItem value="date_asc">Más antiguos primero</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <Accordion type="single" collapsible className="w-full">
                  <AccordionItem value="retailers">
                    <AccordionTrigger className="py-2">
                      Retailers
                      {selectedRetailers.length > 0 && (
                        <Badge variant="secondary" className="ml-2 text-xs">
                          {selectedRetailers.length}
                        </Badge>
                      )}
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="grid grid-cols-2 gap-2">
                        {retailers.map(retailer => (
                          <div key={retailer} className="flex items-center space-x-2">
                            <Checkbox 
                              id={`retailer-${retailer}`} 
                              checked={selectedRetailers.includes(retailer)}
                              onCheckedChange={() => toggleRetailer(retailer)}
                            />
                            <Label 
                              htmlFor={`retailer-${retailer}`}
                              className="text-sm cursor-pointer"
                            >
                              {retailer}
                            </Label>
                          </div>
                        ))}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                  
                  <AccordionItem value="categories">
                    <AccordionTrigger className="py-2">
                      Categorías
                      {selectedCategories.length > 0 && (
                        <Badge variant="secondary" className="ml-2 text-xs">
                          {selectedCategories.length}
                        </Badge>
                      )}
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="grid grid-cols-2 gap-2">
                        {categories.map(category => (
                          <div key={category} className="flex items-center space-x-2">
                            <Checkbox 
                              id={`category-${category}`} 
                              checked={selectedCategories.includes(category)}
                              onCheckedChange={() => toggleCategory(category)}
                            />
                            <Label 
                              htmlFor={`category-${category}`}
                              className="text-sm cursor-pointer"
                            >
                              {category}
                            </Label>
                          </div>
                        ))}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                  
                  <AccordionItem value="price">
                    <AccordionTrigger className="py-2">
                      Rango de precios
                      {!(priceRange[0] === 0 && priceRange[1] === 5000) && (
                        <Badge variant="secondary" className="ml-2 text-xs">
                          ${priceRange[0]} - ${priceRange[1]}
                        </Badge>
                      )}
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-4 px-1 pt-2">
                        <Slider 
                          value={priceRange}
                          min={0}
                          max={5000}
                          step={100}
                          onValueChange={handlePriceChange}
                        />
                        <div className="flex items-center justify-between text-sm">
                          <span>${priceRange[0]}</span>
                          <span>${priceRange[1]}</span>
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
                
                <Button 
                  className="w-full"
                  onClick={() => setShowFilters(false)}
                >
                  Aplicar filtros
                </Button>
              </div>
            </PopoverContent>
          </Popover>
          
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
        
        {/* Badges de filtros activos */}
        {activeFiltersCount > 0 && (
          <div className="flex flex-wrap gap-2">
            {sortBy && (
              <Badge variant="secondary" className="flex items-center gap-1 pr-1">
                {sortBy.includes('name') ? 'Nombre' : 
                 sortBy.includes('price') ? 'Precio' : 
                 sortBy.includes('retailer') ? 'Retailer' : 'Fecha'} 
                {sortBy.includes('asc') ? '↑' : '↓'}
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-4 w-4" 
                  onClick={() => setSortBy("")}
                >
                  <X className="h-3 w-3" />
                </Button>
              </Badge>
            )}
            
            {selectedRetailers.length > 0 && (
              <Badge variant="secondary" className="flex items-center gap-1 pr-1">
                Retailers ({selectedRetailers.length})
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-4 w-4" 
                  onClick={() => setSelectedRetailers([])}
                >
                  <X className="h-3 w-3" />
                </Button>
              </Badge>
            )}
            
            {selectedCategories.length > 0 && (
              <Badge variant="secondary" className="flex items-center gap-1 pr-1">
                Categorías ({selectedCategories.length})
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-4 w-4" 
                  onClick={() => setSelectedCategories([])}
                >
                  <X className="h-3 w-3" />
                </Button>
              </Badge>
            )}
            
            {!(priceRange[0] === 0 && priceRange[1] === 5000) && (
              <Badge variant="secondary" className="flex items-center gap-1 pr-1">
                ${priceRange[0]} - ${priceRange[1]}
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-4 w-4" 
                  onClick={() => setPriceRange([0, 5000])}
                >
                  <X className="h-3 w-3" />
                </Button>
              </Badge>
            )}
          </div>
        )}
      </div>

      {searched && (
        <div>
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">
                  {products.length > 0 ? (
                    <>
                      Resultados para "{searchQuery}"{" "}
                      <span className="text-muted-foreground text-base">({products.length})</span>
                    </>
                  ) : (
                    `No se encontraron resultados para "${searchQuery}"`
                  )}
                </h2>
                
                {/* Selector de ordenamiento en línea (visible solo con resultados) */}
                {products.length > 0 && (
                  <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger className="w-auto min-w-[180px]">
                      <span className="flex items-center gap-1">
                        <ArrowUpDown className="h-4 w-4" />
                        <SelectValue placeholder="Ordenar por" />
                      </span>
                    </SelectTrigger>
                    <SelectContent align="end">
                      <SelectItem value="name_asc">Nombre (A-Z)</SelectItem>
                      <SelectItem value="name_desc">Nombre (Z-A)</SelectItem>
                      <SelectItem value="price_asc">Precio (menor a mayor)</SelectItem>
                      <SelectItem value="price_desc">Precio (mayor a menor)</SelectItem>
                      <SelectItem value="retailer_asc">Retailer (A-Z)</SelectItem>
                      <SelectItem value="date_desc">Más recientes primero</SelectItem>
                      <SelectItem value="date_asc">Más antiguos primero</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              </div>
              <ProductList products={products} />
              {products.length > 0 && (
                <Pagination className="mt-6">
                  <PaginationContent>
                    {page > 1 && (
                      <PaginationItem>
                        <PaginationPrevious
                          href="#"
                          onClick={(e) => {
                            e.preventDefault()
                            fetchProducts(page - 1)
                          }}
                        />
                      </PaginationItem>
                    )}

                    {page > 2 && (
                      <PaginationItem>
                        <PaginationLink href="#" onClick={(e) => {
                          e.preventDefault()
                          fetchProducts(1)
                        }}>
                          1
                        </PaginationLink>
                      </PaginationItem>
                    )}

                    {page > 3 && (
                      <PaginationItem>
                        <PaginationEllipsis />
                      </PaginationItem>
                    )}

                    {[-1, 0, 1].map((offset) => {
                      const p = page + offset
                      if (p > 0 && p <= totalPages) {
                        return (
                          <PaginationItem key={p}>
                            <PaginationLink
                              href="#"
                              isActive={p === page}
                              onClick={(e) => {
                                e.preventDefault()
                                fetchProducts(p)
                              }}
                            >
                              {p}
                            </PaginationLink>
                          </PaginationItem>
                        )
                      }
                      return null
                    })}

                    {page < totalPages - 2 && (
                      <PaginationItem>
                        <PaginationEllipsis />
                      </PaginationItem>
                    )}

                    {page < totalPages - 1 && (
                      <PaginationItem>
                        <PaginationLink href="#" onClick={(e) => {
                          e.preventDefault()
                          fetchProducts(totalPages)
                        }}>
                          {totalPages}
                        </PaginationLink>
                      </PaginationItem>
                    )}

                    {page < totalPages && (
                      <PaginationItem>
                        <PaginationNext
                          href="#"
                          onClick={(e) => {
                            e.preventDefault()
                            fetchProducts(page + 1)
                          }}
                        />
                      </PaginationItem>
                    )}
                  </PaginationContent>
                </Pagination>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}