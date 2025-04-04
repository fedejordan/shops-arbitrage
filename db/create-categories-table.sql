ALTER TABLE public.products
ADD COLUMN category_id INTEGER;
CREATE TABLE public.categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE public.retailer_categories (
    id SERIAL PRIMARY KEY,
    retailer_id INTEGER NOT NULL REFERENCES public.retailers(id),
    name TEXT NOT NULL,
    category_id INTEGER REFERENCES public.categories(id),
    UNIQUE(retailer_id, name) -- evita duplicados
);
INSERT INTO retailer_categories (retailer_id, name)
SELECT DISTINCT retailer_id, category
FROM products
WHERE category IS NOT NULL
ON CONFLICT DO NOTHING;
