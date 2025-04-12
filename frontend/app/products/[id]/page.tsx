"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Image from "next/image"
import { Skeleton } from "@/components/ui/skeleton"
import { formatCurrency, timeAgo } from "@/lib/utils"
import ReactMarkdown from "react-markdown"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  ReferenceLine
} from "recharts"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ShoppingCart, Heart, Share2, ArrowLeft, TrendingDown, TrendingUp, Info, History } from "lucide-react"
import Link from "next/link"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

export default function ProductPage() {
  const { id } = useParams()
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const [similarProducts, setSimilarProducts] = useState([])
  const [wishlistStatus, setWishlistStatus] = useState(false)
  
  // Calcular si es el precio más bajo histórico
  const [isPriceLowest, setIsPriceLowest] = useState(false)
  const [priceDropPercentage, setPriceDropPercentage] = useState(0)

  useEffect(() => {
    // Cargar el producto principal
    fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/products/${id}`)
      .then(res => res.json())
      .then(data => {
        setProduct(data)
        setLoading(false)
      })
      .catch(err => {
        console.error("Error:", err)
        setLoading(false)
      })

    // Cargar historial de precios en paralelo
    fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/products/${id}/history`)
      .then(res => res.json())
      .then(data => {
        setHistory(data)
        setHistoryLoading(false)
        
        // Verificar si el precio actual es el más bajo
        if (data.length > 0 && product) {
          const lowestHistoricalPrice = Math.min(...data.map(h => h.final_price))
          setIsPriceLowest(product.final_price <= lowestHistoricalPrice)
          
          // Calcular el porcentaje de descuento actual
          if (product.original_price > 0) {
            const discount = ((product.original_price - product.final_price) / product.original_price) * 100
            setPriceDropPercentage(Math.round(discount))
          }
        }
      })
      .catch(err => {
        console.error("Error cargando historial:", err)
        setHistoryLoading(false)
      })

    // Cargar productos similares en paralelo
    fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/products/${id}/similar`)
      .then(res => res.json())
      .then(data => {
        setSimilarProducts(data.slice(0, 4)) // Limitamos a 4 productos similares
      })
      .catch(err => console.error("Error cargando similares:", err))
  }, [id, product])

  // Generar los datos para el gráfico
  const prepareChartData = () => {
    if (!history.length || !product) return []
    
    let chartData = history.map(h => ({
      date: new Date(h.date).toISOString().split("T")[0],
      final_price: h.final_price,
      original_price: h.original_price || null
    }))
    
    // Añadir el punto actual si no existe
    const currentPoint = {
      date: new Date(product.updated_date).toISOString().split("T")[0],
      final_price: product.final_price,
      original_price: product.original_price || null
    }
    
    const exists = chartData.some(
      d => d.date === currentPoint.date && d.final_price === currentPoint.final_price
    )
    
    if (!exists) {
      chartData.push(currentPoint)
    }
    
    // Ordenar por fecha
    return chartData.sort((a, b) => 
      new Date(a.date).getTime() - new Date(b.date).getTime()
    )
  }
  
  const chartData = prepareChartData()
  
  // Calcular el precio mínimo para la línea de referencia
  const minPrice = chartData.length > 0 
    ? Math.min(...chartData.map(item => item.final_price)) 
    : 0
  
  const toggleWishlist = () => {
    setWishlistStatus(!wishlistStatus)
    // Aquí iría la lógica para añadir/eliminar de favoritos
  }

  // Componente de skeleton para la carga
  if (loading || !product) {
    return (
      <div className="container max-w-6xl mx-auto px-4 py-8">
        <div className="flex items-center space-x-2 mb-6">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-24" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <Skeleton className="aspect-square rounded-lg" />
          <div className="space-y-4">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-6 w-1/3" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        </div>
        <div className="mt-8">
          <Skeleton className="h-6 w-48 mb-4" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    )
  }

  return (
    <div className="container max-w-6xl mx-auto px-4 py-8">
      {/* Breadcrumb y navegación */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center text-sm text-gray-500">
          <Link href="/products" className="flex items-center hover:text-primary transition-colors">
            <ArrowLeft className="h-4 w-4 mr-1" />
            Volver a productos
          </Link>
          <span className="mx-2">/</span>
          <span className="truncate max-w-[200px]">{product.title}</span>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => toggleWishlist()}>
            <Heart className={`h-4 w-4 mr-1 ${wishlistStatus ? 'fill-rose-500 text-rose-500' : ''}`} />
            {wishlistStatus ? 'Guardado' : 'Guardar'}
          </Button>
          <Button variant="outline" size="sm">
            <Share2 className="h-4 w-4 mr-1" />
            Compartir
          </Button>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Imagen del producto */}
        <div className="relative bg-white rounded-lg overflow-hidden shadow-sm border">
          <div className="relative aspect-square">
            <Image
              src={product.image || "/placeholder.svg"}
              alt={product.title}
              fill
              className="object-contain p-4"
              sizes="(max-width: 768px) 100vw, 50vw"
              priority
            />
          </div>
          
          {/* Etiquetas de descuento o mejor precio */}
          {priceDropPercentage > 0 && (
            <Badge className="absolute top-4 left-4 bg-red-500">
              {priceDropPercentage}% DESCUENTO
            </Badge>
          )}
          
          {isPriceLowest && (
            <Badge className="absolute top-4 right-4 bg-green-500 flex items-center">
              <TrendingDown className="h-3 w-3 mr-1" />
              PRECIO MÁS BAJO
            </Badge>
          )}
        </div>

        {/* Información del producto */}
        <div className="space-y-6">
          <div>
            <div className="flex items-center">
              <Badge variant="outline" className="mb-2">
                {product.retailer?.name}
              </Badge>
            </div>
            <h1 className="text-3xl font-bold">{product.title}</h1>
          </div>

          {/* Precios */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-primary">
                {formatCurrency(product.final_price)}
              </span>
              
              {product.original_price > product.final_price && (
                <span className="text-lg text-gray-500 line-through">
                  {formatCurrency(product.original_price)}
                </span>
              )}
            </div>
            
            <div className="mt-2 text-sm text-gray-500">
              Actualizado: {timeAgo(product.updated_date)}
            </div>
          </div>

          {/* Botones de acción */}
          <div className="flex gap-3 flex-wrap">
            <Button className="flex-1" size="lg" asChild>
              <a
                href={product.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center"
              >
                <ShoppingCart className="h-5 w-5 mr-2" />
                Comprar ahora
              </a>
            </Button>
            
            <Button variant="outline" size="lg" className="flex-1">
              <Heart className="h-5 w-5 mr-2" />
              Añadir a favoritos
            </Button>
          </div>

          {/* Alerta de precio si hay ofertas */}
          {priceDropPercentage > 10 && (
            <Alert className="bg-amber-50 border-amber-200">
              <Info className="h-4 w-4 text-amber-500" />
              <AlertTitle className="text-amber-700">¡Oferta destacada!</AlertTitle>
              <AlertDescription className="text-amber-600">
                Este producto tiene un {priceDropPercentage}% de descuento sobre su precio original.
              </AlertDescription>
            </Alert>
          )}
        </div>
      </div>

      {/* Pestañas de contenido */}
      <Tabs defaultValue="description" className="mt-10">
        <TabsList className="grid grid-cols-3 w-full max-w-md">
          <TabsTrigger value="description">Descripción</TabsTrigger>
          <TabsTrigger value="prices">
            <History className="h-4 w-4 mr-1" />
            Historial
          </TabsTrigger>
          <TabsTrigger value="similar">Similares</TabsTrigger>
        </TabsList>
        
        {/* Pestaña: Descripción */}
        <TabsContent value="description" className="mt-6">
          {product.ai_description ? (
            <Card>
              <CardContent className="pt-6">
                <div className="prose prose-gray max-w-none dark:prose-invert">
                  <ReactMarkdown>{product.ai_description}</ReactMarkdown>
                </div>
              </CardContent>
            </Card>
          ) : (
            <p className="text-gray-500 italic">No hay descripción disponible para este producto.</p>
          )}
        </TabsContent>
        
        {/* Pestaña: Historial de precios */}
        <TabsContent value="prices" className="mt-6">
          <Card>
            <CardContent className="pt-6">
              <h3 className="text-lg font-medium mb-4 flex items-center">
                <TrendingUp className="h-5 w-5 mr-2 text-primary" />
                Historial de precios
              </h3>
              
              {historyLoading ? (
                <p className="text-sm text-gray-500">Cargando historial...</p>
              ) : chartData.length <= 1 ? (
                <p className="text-sm text-gray-500">Este producto ha mantenido el mismo precio desde que comenzamos a seguirlo.</p>
              ) : (
                <div className="w-full h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis 
                        dataKey="date" 
                        tickFormatter={(date) => {
                          const d = new Date(date)
                          return `${d.getDate()}/${d.getMonth() + 1}`
                        }}
                        tick={{ fontSize: 12 }}
                      />
                      <YAxis tickFormatter={(value) => `$${value}`} tick={{ fontSize: 12 }} />
                      <Tooltip 
                        formatter={(value) => [`$${value.toFixed(2)}`, 'Precio']}
                        labelFormatter={(date) => new Date(date).toLocaleDateString()}
                        contentStyle={{ borderRadius: '8px' }}
                      />
                      <ReferenceLine 
                        y={minPrice} 
                        stroke="#10B981" 
                        strokeDasharray="3 3"
                        label={{ value: 'Mínimo', position: 'insideBottomRight', fill: '#10B981', fontSize: 12 }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="final_price" 
                        stroke="#3B82F6" 
                        name="Precio final"
                        strokeWidth={2}
                        dot={{ r: 4 }}
                        activeDot={{ r: 6, stroke: '#3B82F6', strokeWidth: 2 }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="original_price" 
                        stroke="#EF4444" 
                        name="Precio original"
                        strokeWidth={1.5}
                        strokeDasharray="4 4"
                        dot={{ r: 3 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
              
              {/* Estadísticas adicionales */}
              {!historyLoading && chartData.length > 1 && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500">Precio más bajo</p>
                    <p className="text-lg font-medium text-green-600">
                      {formatCurrency(minPrice)}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500">Precio más alto</p>
                    <p className="text-lg font-medium text-red-600">
                      {formatCurrency(Math.max(...chartData.map(item => item.final_price)))}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500">Precio promedio</p>
                    <p className="text-lg font-medium">
                      {formatCurrency(chartData.reduce((acc, curr) => acc + curr.final_price, 0) / chartData.length)}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500">Seguimiento</p>
                    <p className="text-lg font-medium">
                      {chartData.length} días
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        {/* Pestaña: Productos similares */}
        <TabsContent value="similar" className="mt-6">
          <Card>
            <CardContent className="pt-6">
              {similarProducts.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {similarProducts.map(p => (
                    <Link
                      key={p.id}
                      href={`/products/${p.id}`}
                      className="group"
                    >
                      <div className="border rounded-lg overflow-hidden hover:shadow-md transition-all group-hover:border-primary">
                        <div className="h-40 relative bg-white p-2">
                          <Image
                            src={p.image || "/placeholder.svg"}
                            alt={p.title}
                            fill
                            className="object-contain p-2"
                          />
                        </div>
                        <div className="p-3">
                          <p className="font-medium text-sm line-clamp-2 group-hover:text-primary transition-colors">
                            {p.title}
                          </p>
                          <div className="mt-2 flex justify-between items-baseline">
                            <p className="text-primary font-bold">
                              {formatCurrency(p.final_price)}
                            </p>
                            {p.original_price > p.final_price && (
                              <p className="text-xs text-gray-500 line-through">
                                {formatCurrency(p.original_price)}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 italic">No hay productos similares disponibles.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}