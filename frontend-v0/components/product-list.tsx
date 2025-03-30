import Image from "next/image"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { Product } from "@/lib/types"
import { formatCurrency, calculateDiscount } from "@/lib/utils"
import { ExternalLink } from "lucide-react"

export function ProductList({ products }: { products: Product[] }) {
  if (products.length === 0) {
    return null
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {products.map((product) => (
        <Card key={product.id} className="overflow-hidden">
          <CardContent className="p-0">
            <div className="flex flex-col sm:flex-row">
              <div className="relative h-48 sm:w-1/3 bg-gray-100">
                {product.image ? (
                  <Image
                    src={product.image || "/placeholder.svg"}
                    alt={product.title}
                    fill
                    className="object-contain p-2"
                  />
                ) : (
                  <div className="flex h-full items-center justify-center text-gray-400">Sin imagen</div>
                )}
              </div>
              <div className="p-4 sm:w-2/3">
                <div className="flex flex-col h-full justify-between">
                  <div>
                    <h3 className="font-medium line-clamp-2 mb-1">{product.title}</h3>
                    <Badge variant="outline" className="mb-2">
                      {product.category || "Sin categoría"}
                    </Badge>
                  </div>

                  <div className="mt-2">
                    <div className="flex items-baseline gap-2">
                      <span className="text-xl font-bold">{formatCurrency(product.final_price)}</span>
                      {product.original_price > product.final_price && (
                        <span className="text-sm text-gray-500 line-through">
                          {formatCurrency(product.original_price)}
                        </span>
                      )}
                    </div>

                    {product.original_price > product.final_price && (
                      <div className="text-sm text-green-600 font-medium">
                        {calculateDiscount(product.original_price, product.final_price)}% OFF
                      </div>
                    )}

                    <a
                      href={product.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-flex items-center text-sm text-primary hover:underline"
                    >
                      Ver producto <ExternalLink className="ml-1 h-3 w-3" />
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

