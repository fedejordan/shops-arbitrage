// app/admin/layout.tsx
import Link from "next/link"

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="w-64 bg-gray-100 p-4">
        <h2 className="text-lg font-bold mb-4">Admin Panel</h2>
        <nav className="space-y-2">
          <Link href="/admin/categories" className="block text-sm hover:underline">Retailer Categories</Link>
          <Link href="/admin/products" className="block text-sm hover:underline">Productos sin Categoría</Link>
        </nav>
      </aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  )
}
