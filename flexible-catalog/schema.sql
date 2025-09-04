CREATE DATABASE IF NOT EXISTS catalog;
USE catalog;

DROP TABLE IF EXISTS products;

CREATE TABLE products (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10,2) NOT NULL,
    specs JSON,

    -- Generated (stored) columns
    ram_gb INT GENERATED ALWAYS AS (CAST(JSON_UNQUOTE(JSON_EXTRACT(specs, '$.ram')) AS UNSIGNED)) STORED,
    gpu VARCHAR(100) GENERATED ALWAYS AS (JSON_UNQUOTE(JSON_EXTRACT(specs, '$.gpu'))) STORED,
    screen_in DECIMAL(5,2) GENERATED ALWAYS AS (CAST(JSON_UNQUOTE(JSON_EXTRACT(specs, '$.screen_inches')) AS DECIMAL(5,2))) STORED,
    battery_mah INT GENERATED ALWAYS AS (CAST(JSON_UNQUOTE(JSON_EXTRACT(specs, '$.battery')) AS UNSIGNED)) STORED,

    -- Constraints
    CONSTRAINT chk_price_nonneg CHECK (price >= 0),
    CONSTRAINT chk_specs_valid CHECK (JSON_VALID(specs))
);

-- Indexes for fast queries
CREATE INDEX idx_ram ON products(ram_gb);
CREATE INDEX idx_gpu ON products(gpu);
CREATE INDEX idx_screen ON products(screen_in);
CREATE INDEX idx_battery ON products(battery_mah);

-- Trigger to normalize JSON before insert
DELIMITER //
CREATE TRIGGER validate_specs
BEFORE INSERT ON products
FOR EACH ROW
BEGIN
    SET NEW.specs = JSON_MERGE_PATCH('{}', NEW.specs);
END;//
DELIMITER ;

-- Analytics view
CREATE OR REPLACE VIEW products_summary AS
SELECT category, COUNT(*) as total, AVG(price) as avg_price
FROM products
GROUP BY category;
