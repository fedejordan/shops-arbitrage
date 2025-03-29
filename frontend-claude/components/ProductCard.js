import Image from 'next/image';

export default function ProductCard({ product }) {
  // Calcular descuento si hay precio original y final
  const discount = product.original_price && product.final_price
    ? Math.round(((product.original_price - product.final_price) / product.original_price) * 100)
    : 0;

  // Obtener dominio de la URL para mostrar la tienda
  const getStoreName = (url) => {
    try {
      const domain = new URL(url).hostname.replace('www.', '');
      return domain.split('.')[0];
    } catch (e) {
      return 'desconocida';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
      <div className="relative h-48 bg-gray-200">
        {product.image ? (
          <Image
            src={product.image}
            alt={product.title}
            layout="fill"
            objectFit="contain"
            className="p-2"
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <span className="text-gray-400">Sin imagen</span>
          </div>
        )}
        
        {discount > 0 && (
          <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded-md text-sm font-bold">
            -{discount}%
          </div>
        )}
      </div>
      
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-800 line-clamp-2 h-14">{product.title}</h3>
        
        <div className="mt-2 text-sm text-gray-500">
          <span className="capitalize">
            {product.category || 'Sin categoría'}
          </span>
          <span className="ml-2 px-2 py-1 bg-gray-100 rounded-full text-xs capitalize">
            {getStoreName(product.url)}
          </span>
        </div>
        
        <div className="mt-3 flex items-end">
          {product.original_price && product.original_price !== product.final_price && (
            <span className="text-sm text-gray-500 line-through mr-2">
              ${product.original_price.toLocaleString('es-AR')}
            </span>
          )}
          <span className="text-xl font-bold text-primary">
            ${product.final_price.toLocaleString('es-AR')}
          </span>
        </div>
        
        <a
          href={product.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 block text-center bg-primary hover:bg-secondary text-white py-2 px-4 rounded transition-colors duration-300"
        >
          Ver producto
        </a>
      </div>
    </div>
  );
}