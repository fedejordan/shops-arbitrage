import Image from "next/image"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { Product } from "@/lib/types"
import { formatCurrency, calculateDiscount, timeAgo } from "@/lib/utils"
import { ExternalLink } from "lucide-react"
import Link from "next/link"

export function ProductList({ products }: { products: Product[] }) {
  if (products.length === 0) {
    return null
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {products.map((product) => {
        console.log(product.title + " - " + product.category_name + " - " + product.added_date + " - " + product.updated_date)
        console.log(new Date(product.added_date))
        return (
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
                  <div className="flex flex-wrap gap-2 mb-2">
                    <Badge variant="outline">{product.category_name || "Sin categoría"}</Badge>
                    {product.retailer?.name && (
                      <Badge variant="secondary" className="text-xs">
                        {product.retailer.name}
                      </Badge>
                    )}
                    {product.added_date && (
                      <Badge variant="outline" className="text-xs text-gray-500">
                        Agregado hace {timeAgo(product.added_date)}
                      </Badge>
                    )}
                    {product.updated_date && (
                      <Badge variant="outline" className="text-xs text-gray-400">
                        Editado hace {timeAgo(product.updated_date)}
                      </Badge>
                    )}
                  </div>
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

                    <Link
                      href={`/products/${product.id}`}
                      className="mt-2 inline-flex items-center text-sm text-primary hover:underline"
                    >
                      Ver detalle <ExternalLink className="ml-1 h-3 w-3" />
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )})}
    </div>
  )
}

