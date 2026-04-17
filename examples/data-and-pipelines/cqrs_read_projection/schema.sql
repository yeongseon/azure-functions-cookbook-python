CREATE TABLE IF NOT EXISTS order_read_models (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    status TEXT NOT NULL,
    item_count INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    updated_at TEXT NOT NULL
);
