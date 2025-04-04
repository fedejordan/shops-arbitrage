'use client'

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import {
    Select,
    SelectTrigger,
    SelectValue,
    SelectContent,
    SelectItem
  } from "@/components/ui/select"

type Category = { id: number, name: string }
type Product = {
    id: number
    title: string
    url: string
    image: string | null
    category_id: number | null
    suggestedCategoryId?: number | null
  }  
const LIMIT = 50

export default function ManageUncategorizedProducts() {
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [selected, setSelected] = useState<Record<number, number | null>>({})
  const [loadingIds, setLoadingIds] = useState<Set<number>>(new Set())
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loadingMore, setLoadingMore] = useState(false)

  const url = process.env.NEXT_PUBLIC_API_BASE_URL

  useEffect(() => {
    fetch(`${url}/categories`).then(res => res.json()).then(setCategories)
    fetch(`${url}/products/uncategorized/count`).then(res => res.json()).then(data => {
      setTotal(data.count)
    })
    loadProducts(0)
  }, [])

  const loadProducts = async (currentOffset: number) => {
    setLoadingMore(true)
    const res = await fetch(`${url}/products/uncategorized?offset=${currentOffset}&limit=${LIMIT}`)
    const data: Product[] = await res.json()
    setProducts(prev => [...prev, ...data])
    const initial: Record<number, number | null> = {}
    data.forEach(p => { initial[p.id] = p.category_id })
    setSelected(prev => ({ ...prev, ...initial }))
    setOffset(currentOffset + LIMIT)
    setLoadingMore(false)
  }

  const handleAssign = async (product_id: number) => {
    const category_id = selected[product_id]
    if (!category_id) return

    setLoadingIds(prev => new Set(prev).add(product_id))
    try {
      await fetch(`${url}/products/${product_id}/assign-category?category_id=${category_id}`, {
        method: "PATCH"
      })
      setProducts(prev => prev.filter(p => p.id !== product_id))
    } catch (e) {
      console.error("Error assigning category", e)
    } finally {
      setLoadingIds(prev => {
        const updated = new Set(prev)
        updated.delete(product_id)
        return updated
      })
    }
  }

  const handleSuggest = async (product_id: number) => {
    setLoadingIds(prev => new Set(prev).add(product_id))
    try {
      const res = await fetch(`${url}/products/${product_id}/suggest-category`, { method: "POST" })
      const data = await res.json()
      const suggestedId = data.suggested_category_id
  
      setProducts(prev =>
        prev.map(p =>
          p.id === product_id ? { ...p, suggestedCategoryId: suggestedId } : p
        )
      )
      setSelected(prev => ({ ...prev, [product_id]: suggestedId }))
    } catch (e) {
      console.error("Error getting suggestion", e)
    } finally {
      setLoadingIds(prev => {
        const updated = new Set(prev)
        updated.delete(product_id)
        return updated
      })
    }
  }
  

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold">Productos sin categoría</h1>
      <p className="text-sm text-muted-foreground">
        {total} producto{total !== 1 ? "s" : ""} sin categorizar
      </p>
      {products.map(p => (
        <div key={p.id} className="flex gap-4 items-center border-b py-2">
          <a
            href={p.url}
            target="_blank"
            rel="noopener noreferrer"
            className="w-1/3 truncate text-blue-600 hover:underline"
            title={p.title}
            >
            {p.title}
        </a>
          <Select onValueChange={(val) => setSelected(prev => ({ ...prev, [p.id]: +val }))}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Elegí una categoría" />
            </SelectTrigger>
            <SelectContent>
              {categories.map(c => (
                <SelectItem key={c.id} value={String(c.id)}>{c.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          {p.suggestedCategoryId && (
            <p className="text-xs text-muted-foreground">
                Sugerido: {
                categories.find(c => c.id === p.suggestedCategoryId)?.name || "?"
                }
            </p>
            )}
          <Button onClick={() => handleAssign(p.id)} disabled={loadingIds.has(p.id)}>
            {loadingIds.has(p.id) ? "Asignando..." : "Asignar"}
          </Button>
          <Button
            variant="outline"
            onClick={() => handleSuggest(p.id)}
            disabled={loadingIds.has(p.id)}
            >
            {loadingIds.has(p.id) ? "Consultando..." : "Autoasignar"}
          </Button>
        </div>
      ))}
      {offset < total && (
        <Button onClick={() => loadProducts(offset)} disabled={loadingMore}>
          {loadingMore ? "Cargando..." : "Cargar más"}
        </Button>
      )}
    </div>
  )
}
