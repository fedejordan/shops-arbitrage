-- Agregar columna retailer_id a la tabla products
ALTER TABLE products
ADD COLUMN retailer_id INTEGER REFERENCES retailers(id);
