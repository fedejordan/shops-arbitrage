import { SearchForm } from "@/components/search-form"

export default function Home() {
  return (
    <main className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-center mb-8">Arbitraje de Productos</h1>
      <div className="max-w-3xl mx-auto">
        <SearchForm />
      </div>
    </main>
  )
}

