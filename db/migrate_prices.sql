-- 1. Renombrar las columnas originales
ALTER TABLE products
RENAME COLUMN original_price TO original_price_text;

ALTER TABLE products
RENAME COLUMN final_price TO final_price_text;

-- 2. Agregar nuevas columnas numéricas
ALTER TABLE products
ADD COLUMN original_price NUMERIC(10,2),
ADD COLUMN final_price NUMERIC(10,2);

-- 3. Limpiar y convertir precios
UPDATE products
SET
  original_price = CASE
    WHEN original_price_text IS NOT NULL AND original_price_text <> '' THEN
      REPLACE(REPLACE(original_price_text, '.', ''), ',', '.')::NUMERIC
    ELSE NULL
  END,
  final_price = CASE
    WHEN final_price_text IS NOT NULL AND final_price_text <> '' THEN
      REPLACE(REPLACE(final_price_text, '.', ''), ',', '.')::NUMERIC
    ELSE NULL
  END;

-- 4. (Opcional) Eliminar columnas antiguas de texto
ALTER TABLE products
DROP COLUMN original_price_text,
DROP COLUMN final_price_text;
