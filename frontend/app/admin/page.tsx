// app/admin/page.tsx

export default function AdminHome() {
    return (
      <div className="p-6 space-y-4">
        <h1 className="text-2xl font-bold">Panel de Administración</h1>
        <p className="text-muted-foreground text-sm">
          Bienvenido al panel. Desde aquí podés gestionar las categorías y productos.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
          <a href="/admin/categories" className="p-4 border rounded-lg hover:bg-gray-50 transition">
            <h2 className="font-semibold text-lg">Retailer Categories</h2>
            <p className="text-sm text-muted-foreground">Asignar categorías propias a categorías de retailers.</p>
          </a>
          <a href="/admin/products" className="p-4 border rounded-lg hover:bg-gray-50 transition">
            <h2 className="font-semibold text-lg">Productos sin Categoría</h2>
            <p className="text-sm text-muted-foreground">Categorizar productos que no fueron asignados automáticamente.</p>
          </a>
        </div>
      </div>
    )
  }
  