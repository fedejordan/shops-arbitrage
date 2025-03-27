CREATE TABLE fravega_productos (
    id SERIAL PRIMARY KEY,
    title TEXT,
    original_price TEXT,
    final_price TEXT,
    url TEXT UNIQUE,
    image TEXT,
    category TEXT,
	added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
