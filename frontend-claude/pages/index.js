import { useState } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import SearchBar from '../components/SearchBar';
import ProductCard from '../components/ProductCard';

export default function Home() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (query) => {
    setLoading(true);
    setError(null);
    setSearched(true);
    
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/products/search`, {
        params: { q: query }
      });
      setProducts(response.data);
    } catch (err) {
      console.error('Error al buscar productos:', err);
      setError('Ocurrió un error al buscar los productos. Por favor, intenta nuevamente.');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout title="ProductArbitraje - Inicio">
      <div className="max-w-6xl mx-auto">
        <section className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">Encuentra los mejores precios</h1>
          <p className="text-xl text-gray-600 mb-8">
            Busca productos y compara precios de diferentes tiendas en un solo lugar
          </p>
          
          <SearchBar onSearch={handleSearch} />
        </section>

        <section>
          {loading && (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
            </div>
          )}

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
              <span className="block sm:inline">{error}</span>
            </div>
          )}

          {!loading && searched && products.length === 0 && !error && (
            <div className="text-center py-12">
              <p className="text-xl text-gray-600">No se encontraron productos con tu búsqueda</p>
            </div>
          )}

          {!loading && products.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}

          {!searched && (
            <div className="text-center py-12">
              <p className="text-xl text-gray-600">
                Realiza una búsqueda para ver productos
              </p>
            </div>
          )}
        </section>
      </div>
    </Layout>
  );
}