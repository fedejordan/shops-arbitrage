"use client";

import { useEffect, useState, useMemo } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import { Skeleton } from "@/components/ui/skeleton"; // Asumiendo shadcn/ui
import { Button } from "@/components/ui/button"; // Asumiendo shadcn/ui
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"; // Asumiendo shadcn/ui
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"; // Asumiendo shadcn/ui
import { Terminal } from "lucide-react"; // Icono para la alerta
import { formatCurrency, timeAgo } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import { event } from "@/lib/gtag"


// --- Componente de Alerta de Error (Opcional, puedes ponerlo en otro archivo) ---
function ErrorAlert({ error }) {
  return (
    <Alert variant="destructive" className="my-4">
      <Terminal className="h-4 w-4" />
      <AlertTitle>Error al cargar</AlertTitle>
      <AlertDescription>
        {error || "No se pudo cargar la información. Intenta de nuevo más tarde."}
      </AlertDescription>
    </Alert>
  );
}

// --- Componente Principal ---
export default function ProductPage() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [history, setHistory] = useState([]);
  const [similarProducts, setSimilarProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // Estado para manejar errores

  // Efecto para cargar toda la data inicial
  useEffect(() => {
    if (!id) return; // No hacer nada si no hay ID

    setLoading(true);
    setError(null); // Limpiar errores previos

    const fetchProductData = fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/products/${id}`)
      .then(res => res.ok ? res.json() : Promise.reject(`Error ${res.status}: ${res.statusText}`));

    const fetchHistoryData = fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/products/${id}/history`)
      .then(res => res.ok ? res.json() : Promise.reject(`Error ${res.status}: ${res.statusText}`));

    const fetchSimilarData = fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/products/${id}/similar`)
      .then(res => res.ok ? res.json() : Promise.reject(`Error ${res.status}: ${res.statusText}`));

    Promise.allSettled([fetchProductData, fetchHistoryData, fetchSimilarData])
      .then(results => {
        let fetchError = null;

        // Procesar resultado del producto
        if (results[0].status === 'fulfilled') {
          setProduct(results[0].value);
          event({
            action: "view_product",
            category: "product_page",
            label: results[0].value?.title || "unknown",
          })          
        } else {
          console.error("Error cargando producto:", results[0].reason);
          fetchError = fetchError || results[0].reason;
        }

        // Procesar resultado del historial
        if (results[1].status === 'fulfilled') {
          setHistory(results[1].value);
        } else {
          console.error("Error cargando historial:", results[1].reason);
          // No necesariamente un error fatal, podríamos mostrar el producto sin historial
        }

        // Procesar resultado de similares
        if (results[2].status === 'fulfilled') {
          setSimilarProducts(results[2].value);
        } else {
          console.error("Error cargando similares:", results[2].reason);
          // Tampoco es un error fatal
        }

        if (fetchError) {
          setError(`No se pudo cargar la información principal del producto. ${fetchError}`);
        }
      })
      .catch(err => {
        // Este catch es para errores inesperados en Promise.allSettled (raro)
        console.error("Error inesperado:", err);
        setError("Ocurrió un error inesperado.");
      })
      .finally(() => {
        setLoading(false);
      });

  }, [id]); // Dependencia: id

  // --- Memoización del Chart Data ---
  const chartData = useMemo(() => {
    if (!product || !history) return [];

    let data = history.map(h => ({
      date: new Date(h.date).toISOString().split("T")[0],
      final_price: h.final_price,
      original_price: h.original_price,
    }));

    const currentPoint = {
      date: new Date(product.updated_date).toISOString().split("T")[0],
      final_price: product.final_price,
      original_price: product.original_price,
    };

    const exists = data.some(
      d => d.date === currentPoint.date && d.final_price === currentPoint.final_price
    );

    if (!exists) {
      data.push(currentPoint);
    }

    return data.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [history, product]); // Dependencias: history y product

  // --- Renderizado del Loading State ---
  if (loading) {
    return (
      <div className="p-4 md:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
        <Skeleton className="h-8 w-3/4 mb-4" />
        <div className="grid md:grid-cols-2 gap-8">
          {/* Skeleton para la imagen */}
          <Skeleton className="h-80 md:h-96 w-full rounded-lg" />
          {/* Skeleton para los detalles */}
          <div className="space-y-4">
            <Skeleton className="h-10 w-1/2" /> {/* Precio */}
            <Skeleton className="h-6 w-1/4" /> {/* Precio Original */}
            <Skeleton className="h-20 w-full" /> {/* Descripción */}
            <Skeleton className="h-6 w-1/3" /> {/* Retailer */}
            <Skeleton className="h-6 w-full" /> {/* Fechas */}
            <Skeleton className="h-10 w-36" /> {/* Botón */}
          </div>
        </div>
        {/* Skeleton para historial y similares */}
        <Skeleton className="h-72 w-full mt-8" />
        <Skeleton className="h-56 w-full mt-8" />
      </div>
    );
  }

  // --- Renderizado del Error State ---
  if (error) {
     return (
       <div className="p-4 md:p-6 lg:p-8 max-w-6xl mx-auto">
         <ErrorAlert error={error} />
       </div>
     );
  }

  // --- Renderizado si no se encuentra el producto ---
  if (!product) {
     return (
       <div className="p-4 md:p-6 lg:p-8 max-w-6xl mx-auto text-center">
         <p className="text-xl text-muted-foreground">Producto no encontrado.</p>
       </div>
     );
  }

  // --- Renderizado del Producto ---
  return (
    <div className="p-4 md:p-6 lg:p-8 max-w-6xl mx-auto space-y-8">
      {/* --- Sección Principal: Imagen y Detalles --- */}
      <div className="grid md:grid-cols-2 gap-8">
        {/* Columna Imagen */}
        <div className="relative h-80 md:h-96 bg-slate-100 dark:bg-slate-800 rounded-lg overflow-hidden flex items-center justify-center">
          <Image
            src={product.image || "/placeholder.svg"}
            alt={product.title}
            fill
            sizes="(max-width: 768px) 100vw, 50vw" // Optimización para next/image
            className="object-contain p-4" // Añadido padding para que 'contain' respire
          />
        </div>

        {/* Columna Detalles */}
        <div className="flex flex-col space-y-4">
          <h1 className="text-2xl lg:text-3xl font-bold">{product.title}</h1>

          {/* Precios */}
          <div>
            <p className="text-3xl font-bold text-primary">
              {formatCurrency(product.final_price)}
            </p>
            {product.original_price > product.final_price && (
              <p className="text-md text-gray-500 line-through dark:text-gray-400">
                {formatCurrency(product.original_price)}
              </p>
            )}
          </div>

          {/* Botón de compra */}
          <Button asChild size="lg" className="w-fit">
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() =>
              event({
                action: "click_buy_now",
                category: "product_page",
                label: `${product.title} - ${product.retailer?.name || "unknown"}`,
              })
            }
          >
            Ver en tienda 🛒
          </a>

          </Button>

          {/* Descripción */}
          {product.ai_description && (
            <div className="prose prose-sm dark:prose-invert max-w-none mt-4 text-gray-700 dark:text-gray-300">
              <ReactMarkdown>{product.ai_description}</ReactMarkdown>
            </div>
          )}

          {/* Metadatos */}
          <div className="text-sm text-gray-500 dark:text-gray-400 space-y-1 pt-4 border-t mt-auto">
            <p>Vendido por: <span className="font-medium text-gray-700 dark:text-gray-300">{product.retailer?.name || "Desconocido"}</span></p>
            <p>
              Agregado: {timeAgo(product.added_date)}
            </p>
            <p>
              Última actualización: {timeAgo(product.updated_date)}
            </p>
          </div>
        </div>
      </div>

      {/* --- Sección Historial de Precios --- */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Historial de Precios</CardTitle>
        </CardHeader>
        <CardContent>
          {chartData.length <= 1 ? (
            <p className="text-sm text-muted-foreground">
              No hay suficientes datos históricos para mostrar un gráfico o el precio no ha cambiado.
            </p>
          ) : (
            <div className="w-full h-64 md:h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.5} />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} tickFormatter={(value) => formatCurrency(value, 0)} />
                  <Tooltip
                    formatter={(value, name) => [formatCurrency(value), name]}
                    contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.8)', border: '1px solid #ccc', borderRadius: '4px' }}
                    labelStyle={{ fontWeight: 'bold' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="final_price"
                    stroke="#10B981" // Verde
                    strokeWidth={2}
                    name="Precio Final"
                    dot={false}
                    activeDot={{ r: 6 }}
                  />
                  {/* Mostrar línea de precio original solo si hay diferencia */}
                  {chartData.some(d => d.original_price !== d.final_price) && (
                    <Line
                      type="monotone"
                      dataKey="original_price"
                      stroke="#EF4444" // Rojo
                      strokeWidth={2}
                      name="Precio Original"
                      strokeDasharray="5 5" // Línea punteada para diferenciar
                      dot={false}
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      {/* --- Sección Productos Similares --- */}
      {similarProducts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Productos Similares</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {similarProducts.map((p) => (
                <a // Usar 'Link' de Next.js si es navegación interna
                  key={p.id}
                  href={`/products/${p.id}`} // Asumiendo ruta interna
                  className="border rounded-lg overflow-hidden group hover:shadow-md transition-shadow duration-200 flex flex-col"
                  onClick={() =>
                    event({
                      action: "click_similar_product",
                      category: "product_page",
                      label: p.title,
                    })
                  }
                  
                >
                  <div className="h-40 relative bg-slate-50 dark:bg-slate-800 flex items-center justify-center p-2">
                    <Image
                      src={p.image || "/placeholder.svg"}
                      alt={p.title}
                      fill
                      sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                      className="object-contain group-hover:scale-105 transition-transform duration-200"
                    />
                  </div>
                  <div className="p-3 flex flex-col flex-grow">
                    <p className="text-sm font-medium flex-grow">{p.title}</p>
                    <p className="text-lg font-bold text-primary mt-1">{formatCurrency(p.final_price)}</p>
                  </div>
                </a>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}