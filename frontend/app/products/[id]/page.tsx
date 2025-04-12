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
    ResponsiveContainer
  } from "recharts"
  

export default function ProductPage() {
  const { id } = useParams()
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);


  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/products/${id}`)
      .then(res => res.json())
      .then(data => {
        setProduct(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error:", err);
        setLoading(false);
      });
  
    fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/products/${id}/history`)
      .then(res => res.json())
      .then(data => {
        setHistory(data);
        setHistoryLoading(false);
      })
      .catch(err => {
        console.error("Error cargando historial:", err);
        setHistoryLoading(false);
      });
  }, [id]);
  

  if (loading || !product) {
    return (
      <div className="p-4 space-y-4">
        <Skeleton className="h-6 w-1/2" />
        <Skeleton className="h-96 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  const chartData = history.map(h => ({
    date: new Date(h.date).toLocaleDateString(),
    final_price: h.final_price,
    original_price: h.original_price
  }));  

  return (
    <div className="p-4 max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">{product.title}</h1>
      <div className="relative h-72 bg-gray-100">
        <Image
          src={product.image || "/placeholder.svg"}
          alt={product.title}
          fill
          className="object-contain"
        />
      </div>

      <div>
        <p className="text-xl font-bold">{formatCurrency(product.final_price)}</p>
        {product.original_price > product.final_price && (
          <p className="text-sm text-gray-500 line-through">
            {formatCurrency(product.original_price)}
          </p>
        )}
      </div>

      <div className="text-gray-700">
      {product.ai_description && (
        <div className="prose prose-sm dark:prose-invert max-w-none mt-4">
            <ReactMarkdown>{product.ai_description}</ReactMarkdown>
        </div>
        )}
      </div>

      <div className="text-sm text-gray-500 space-y-1">
        <p>Retailer: {product.retailer?.name}</p>
        <p>
          Agregado: {timeAgo(product.added_date)} – Actualizado: {timeAgo(product.updated_date)}
        </p>
        <a
          href={product.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:underline inline-flex items-center"
        >
          Ver en tienda 🛒
        </a>
      </div>
        <div className="mt-8">
            <h2 className="text-lg font-semibold mb-2">Historial de precios</h2>
            {historyLoading ? (
                <p className="text-sm text-gray-500">Cargando historial...</p>
            ) : history.length === 0 ? (
                <p className="text-sm text-gray-500">Este producto mantuvo el mismo precio.</p>
            ) : (
                <div className="w-full h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
                    <Line type="monotone" dataKey="final_price" stroke="#10B981" name="Precio final" />
                    <Line type="monotone" dataKey="original_price" stroke="#EF4444" name="Precio original" />
                    </LineChart>
                </ResponsiveContainer>
                </div>
            )}
            </div>
    </div>
  )
}
