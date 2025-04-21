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
type RetailerCategory = { id: number, name: string, retailer_id: number, category_id: number | null }

export default function ManageCategories() {
  const [categories, setCategories] = useState<Category[]>([])
  const [retailerCats, setRetailerCats] = useState<RetailerCategory[]>([])
  const [selected, setSelected] = useState<Record<number, number | null>>({})
  const [loadingIds, setLoadingIds] = useState<Set<number>>(new Set())


  useEffect(() => {
    let url = `${process.env.NEXT_PUBLIC_API_BASE_URL}`
    fetch(`${url}/categories`).then(res => res.json()).then(setCategories)
    fetch(`${url}/retailer-categories/unmapped`, ).then(res => res.json()).then(data => {
      setRetailerCats(data)
      const initial: Record<number, number | null> = {}
      data.forEach((rc: RetailerCategory) => { initial[rc.id] = rc.category_id })
      setSelected(initial)
    })
  }, [])

  const handleMap = async (rc_id: number) => {
    let url = `${process.env.NEXT_PUBLIC_API_BASE_URL}`
    const category_id = selected[rc_id]
    if (!category_id) return
  
    setLoadingIds(prev => new Set(prev).add(rc_id))
    try {
      await fetch(`${url}/retailer-categories/${rc_id}/map?category_id=${category_id}`, {
        method: "PATCH",
        credentials: "include",
      })
      setRetailerCats(prev => prev.filter(rc => rc.id !== rc_id))
    } catch (e) {
      console.error("Error mapping category", e)
    } finally {
      setLoadingIds(prev => {
        const updated = new Set(prev)
        updated.delete(rc_id)
        return updated
      })
    }
  }
  

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold">Manage Retailer Categories</h1>
      <p className="text-sm text-muted-foreground">
        {retailerCats.length} categoría{retailerCats.length !== 1 ? "s" : ""} sin mapear
      </p>
      {retailerCats.map(rc => (
        <div key={rc.id} className="flex gap-4 items-center border-b py-2">
          <span className="w-1/3">{rc.name}</span>
          <Select onValueChange={(val) => setSelected(prev => ({ ...prev, [rc.id]: +val }))}>
                <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Elegí una categoría" />
                </SelectTrigger>
                <SelectContent>
                    {categories.map(c => (
                        <SelectItem key={c.id} value={String(c.id)}>
                            {c.name}
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>
            <Button onClick={() => handleMap(rc.id)} disabled={loadingIds.has(rc.id)}>
                {loadingIds.has(rc.id) ? "Mapeando..." : "Map"}
            </Button>
        </div>
      ))}
    </div>
  )
}
