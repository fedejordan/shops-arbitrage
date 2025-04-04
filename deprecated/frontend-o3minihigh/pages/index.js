import { useState } from "react";

export default function Home() {
  const [query, setQuery] = useState("");
  const [products, setProducts] = useState([]);

  const searchProducts = async (e) => {
    e.preventDefault();
    try {
      // Asegúrate de que la URL coincida con la de tu backend
      const res = await fetch(`http://localhost:8000/products?query=${query}`);
      const data = await res.json();
      setProducts(data);
    } catch (error) {
      console.error("Error fetching products:", error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-2xl mx-auto bg-white p-6 rounded shadow">
        <h1 className="text-2xl font-bold mb-4">Arbitraje de Productos</h1>
        <form onSubmit={searchProducts} className="flex mb-4">
          <input
            type="text"
            placeholder="Buscar productos..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-grow border border-gray-300 p-2 rounded-l"
          />
          <button type="submit" className="bg-blue-500 text-white px-4 rounded-r">
            Buscar
          </button>
        </form>
        <div>
          {products.length > 0 ? (
            <ul>
              {products.map((product) => (
                <li key={product.id} className="border-b py-2">
                  <h2 className="font-semibold">{product.title}</h2>
                  <p>
                    Precio original: ${product.original_price} - Precio final: ${product.final_price}
                  </p>
                  {product.image && (
                    <img
                      src={product.image}
                      alt={product.title}
                      className="w-32 h-32 object-cover mt-2"
                    />
                  )}
                  <a
                    href={product.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-500"
                  >
                    Ver producto
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p>No se encontraron productos</p>
          )}
        </div>
      </div>
    </div>
  );
}
