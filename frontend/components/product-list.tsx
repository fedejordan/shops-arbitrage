import Image from "next/image"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { Product } from "@/lib/types"
import { formatCurrency, calculateDiscount, timeAgo } from "@/lib/utils"
import { ExternalLink, ChevronRight, ShoppingCart, Heart, TrendingDown, Clock, Calendar } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"
import { useState } from "react"

export function ProductList({ products }: { products: Product[] }) {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const [hoveredProduct, setHoveredProduct] = useState<string | null>(null)
  const [wishlist, setWishlist] = useState<string[]>([])

  if (products.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No hay productos para mostrar</p>
      </div>
    )
  }

  // Función para alternar productos en la lista de deseos
  const toggleWishlist = (productId: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    setWishlist(prev => 
      prev.includes(productId)
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    )
  }

  // Vista de cuadrícula
  if (viewMode === "grid") {
    return (
      <div>
        <div className="flex justify-end mb-4">
          <div className="flex items-center border rounded-md overflow-hidden">
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "rounded-none border-r h-8",
                viewMode === "list" ? "bg-muted" : "bg-primary text-primary-foreground"
              )}
              onClick={() => setViewMode("grid")}
            >
              Cuadrícula
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "rounded-none",
                viewMode === "list" ? "bg-primary text-primary-foreground" : "bg-muted"
              )}
              onClick={() => setViewMode("list")}
            >
              Lista
            </Button>
          </div>
        </div>
        
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {products.map((product) => (
            <Link
              key={product.id}
              href={`/products/${product.id}`}
              className="group h-full"
              onMouseEnter={() => setHoveredProduct(product.id)}
              onMouseLeave={() => setHoveredProduct(null)}
            >
              <Card className="h-full overflow-hidden transition-all duration-200 hover:shadow-md flex flex-col border-gray-200 hover:border-primary">
                <div className="relative aspect-square bg-white p-2">
                  {/* Badges de descuento */}
                  {product.original_price > product.final_price && (
                    <div className="absolute top-2 left-2 z-10">
                      <Badge className="bg-red-500 hover:bg-red-600">
                        {calculateDiscount(product.original_price, product.final_price)}% OFF
                      </Badge>
                    </div>
                  )}
                  
                  {/* Botón de favorito */}
                  <Button
                    variant="outline"
                    size="icon"
                    className={cn(
                      "absolute top-2 right-2 z-10 h-8 w-8 rounded-full bg-white border-gray-200 opacity-0 group-hover:opacity-100 transition-opacity",
                      wishlist.includes(product.id) && "opacity-100 text-red-500 border-red-200 hover:text-red-600"
                    )}
                    onClick={(e) => toggleWishlist(product.id, e)}
                  >
                    <Heart className={cn(
                      "h-4 w-4",
                      wishlist.includes(product.id) && "fill-red-500"
                    )} />
                    <span className="sr-only">Añadir a favoritos</span>
                  </Button>
                  
                  {/* Imagen del producto */}
                  {product.image ? (
                    <Image
                      src={product.image || "/placeholder.svg"}
                      alt={product.title}
                      fill
                      sizes="(max-width: 640px) 50vw, (max-width: 768px) 33vw, 20vw"
                      className="object-contain p-2 transition-transform duration-300 group-hover:scale-105"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center text-gray-400">
                      Sin imagen
                    </div>
                  )}
                </div>
                
                <CardContent className="p-3 flex-1 flex flex-col justify-between">
                  <div>
                    {/* Tienda */}
                    {product.retailer?.name && (
                      <p className="text-xs text-muted-foreground mb-1 truncate">
                        {product.retailer.name}
                      </p>
                    )}
                    
                    {/* Título */}
                    <h3 className="font-medium line-clamp-2 text-sm group-hover:text-primary transition-colors">
                      {product.title}
                    </h3>
                    
                    {/* Categoría */}
                    {product.category_name && (
                      <Badge variant="outline" className="mt-2 text-xs font-normal px-2 py-0">
                        {product.category_name}
                      </Badge>
                    )}
                  </div>
                  
                  {/* Precio */}
                  <div className="mt-3">
                    <div className="flex items-baseline gap-1">
                      <span className="text-lg font-bold text-primary">
                        {formatCurrency(product.final_price)}
                      </span>
                      {product.original_price > product.final_price && (
                        <span className="text-xs text-gray-500 line-through">
                          {formatCurrency(product.original_price)}
                        </span>
                      )}
                    </div>
                    
                    {/* Botón de acción (visible en hover) */}
                    <div className={cn(
                      "mt-2 transition-opacity duration-200",
                      hoveredProduct === product.id ? "opacity-100" : "opacity-0"
                    )}>
                      <Button
                        size="sm"
                        variant="secondary"
                        className="w-full text-xs h-8"
                      >
                        <ChevronRight className="h-3 w-3 mr-1" />
                        Ver detalles
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    )
  }

  // Vista de lista
  return (
    <div>
      <div className="flex justify-end mb-4">
        <div className="flex items-center border rounded-md overflow-hidden">
          <Button
            variant="ghost"
            size="sm"
            className={cn(
              "rounded-none border-r h-8",
              viewMode === "list" ? "bg-muted" : "bg-primary text-primary-foreground"
            )}
            onClick={() => setViewMode("grid")}
          >
            Cuadrícula
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className={cn(
              "rounded-none",
              viewMode === "list" ? "bg-primary text-primary-foreground" : "bg-muted"
            )}
            onClick={() => setViewMode("list")}
          >
            Lista
          </Button>
        </div>
      </div>
      
      <div className="space-y-4">
        {products.map((product) => (
          <Card key={product.id} className="overflow-hidden hover:shadow-md transition-all border-gray-200 hover:border-primary">
            <Link href={`/products/${product.id}`} className="block">
              <CardContent className="p-0">
                <div className="flex flex-col sm:flex-row">
                  {/* Imagen del producto */}
                  <div className="relative h-52 sm:h-48 sm:w-52 bg-white">
                    {/* Badges de descuento */}
                    {product.original_price > product.final_price && (
                      <div className="absolute top-2 left-2 z-10">
                        <Badge className="bg-red-500 hover:bg-red-600">
                          {calculateDiscount(product.original_price, product.final_price)}% OFF
                        </Badge>
                      </div>
                    )}
                    
                    {product.image ? (
                      <Image
                        src={product.image || "/placeholder.svg"}
                        alt={product.title}
                        fill
                        className="object-contain p-4"
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center text-gray-400">
                        Sin imagen
                      </div>
                    )}
                  </div>
                  
                  {/* Información del producto */}
                  <div className="p-4 sm:w-2/3 flex flex-col h-full justify-between">
                    <div>
                      {/* Tienda y categoría */}
                      <div className="flex flex-wrap gap-2 mb-2">
                        {product.retailer?.name && (
                          <Badge variant="secondary" className="text-xs font-normal">
                            {product.retailer.name}
                          </Badge>
                        )}
                        {product.category_name && (
                          <Badge variant="outline" className="text-xs font-normal">
                            {product.category_name}
                          </Badge>
                        )}
                      </div>
                      
                      {/* Título */}
                      <h3 className="font-medium text-lg mb-2 hover:text-primary transition-colors">
                        {product.title}
                      </h3>
                      
                      {/* Fechas */}
                      <div className="flex flex-wrap text-xs text-muted-foreground mt-2 gap-x-4 gap-y-1">
                        {product.added_date && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <div className="flex items-center">
                                  <Calendar className="h-3 w-3 mr-1" />
                                  Agregado hace {timeAgo(product.added_date)}
                                </div>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>{new Date(product.added_date).toLocaleDateString()}</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                        {product.updated_date && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <div className="flex items-center">
                                  <Clock className="h-3 w-3 mr-1" />
                                  Actualizado hace {timeAgo(product.updated_date)}
                                </div>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>{new Date(product.updated_date).toLocaleDateString()}</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                      </div>
                    </div>

                    {/* Precios y acciones */}
                    <div className="mt-4 flex flex-wrap justify-between items-end gap-4">
                      <div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-2xl font-bold text-primary">
                            {formatCurrency(product.final_price)}
                          </span>
                          {product.original_price > product.final_price && (
                            <span className="text-sm text-gray-500 line-through">
                              {formatCurrency(product.original_price)}
                            </span>
                          )}
                        </div>

                        {product.original_price > product.final_price && (
                          <div className="text-sm text-green-600 font-medium flex items-center">
                            <TrendingDown className="h-3 w-3 mr-1" />
                            {calculateDiscount(product.original_price, product.final_price)}% de descuento
                          </div>
                        )}
                      </div>
                      
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="h-9"
                          onClick={(e) => toggleWishlist(product.id, e)}
                        >
                          <Heart className={cn(
                            "h-4 w-4 mr-1",
                            wishlist.includes(product.id) && "fill-red-500 text-red-500"
                          )} />
                          <span className="sr-only sm:not-sr-only">Guardar</span>
                        </Button>
                        
                        <Button className="h-9">
                          <ShoppingCart className="h-4 w-4 mr-1" />
                          <span className="sr-only sm:not-sr-only">Ver detalles</span>
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Link>
          </Card>
        ))}
      </div>
    </div>
  )
}