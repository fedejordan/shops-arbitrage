
import { SearchForm } from "@/components/search-form"

export default function BuscarPage() {
  return (
    <main className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-center mb-8">Buscar productos</h1>
      <div className="max-w-3xl mx-auto">
        <SearchForm />
      </div>
    </main>
  )
}
