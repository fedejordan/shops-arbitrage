
CREATE TABLE historical_prices (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    original_price NUMERIC,
    final_price NUMERIC,
    date_recorded TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);