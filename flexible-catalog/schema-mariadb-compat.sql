-- schema-mariadb.sql
CREATE DATABASE IF NOT EXISTS catalog;
USE catalog;

-- Main products table with JSON specs
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    specs JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Generated columns (cast JSON values to proper SQL types)
    -- NOTE: some MariaDB versions have subtle differences in JSON return types;
    -- if you hit type or expression errors, see the Migration Checklist below.
    ram_gb INT AS (CAST(JSON_UNQUOTE(JSON_EXTRACT(specs, '$.ram')) AS SIGNED)) STORED,
    storage_gb INT AS (CAST(JSON_UNQUOTE(JSON_EXTRACT(specs, '$.storage')) AS SIGNED)) STORED,
    gpu VARCHAR(100) AS (JSON_UNQUOTE(JSON_EXTRACT(specs, '$.gpu'))) STORED,
    screen_size DECIMAL(3,1) AS (CAST(JSON_UNQUOTE(JSON_EXTRACT(specs, '$.screen_size')) AS DECIMAL(3,1))) STORED,
    battery_mah INT AS (CAST(JSON_UNQUOTE(JSON_EXTRACT(specs, '$.battery_mah')) AS SIGNED)) STORED,
    cpu VARCHAR(100) AS (JSON_UNQUOTE(JSON_EXTRACT(specs, '$.cpu'))) STORED,
    brand VARCHAR(100) AS (JSON_UNQUOTE(JSON_EXTRACT(specs, '$.brand'))) STORED,

    -- Constraints
    CONSTRAINT chk_price CHECK (price > 0),
    CONSTRAINT chk_category CHECK (category IN ('laptop', 'phone', 'tablet', 'desktop', 'monitor', 'accessory')),

    -- Indexes for performance
    INDEX idx_category (category),
    INDEX idx_price (price),
    INDEX idx_ram (ram_gb),
    INDEX idx_storage (storage_gb),
    INDEX idx_gpu (gpu),
    INDEX idx_brand (brand),
    INDEX idx_created (created_at),
    FULLTEXT INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Analytics view
CREATE OR REPLACE VIEW product_summary AS
SELECT 
    category,
    COUNT(*) as total_products,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price,
    AVG(ram_gb) as avg_ram,
    COUNT(DISTINCT brand) as brand_count
FROM products
GROUP BY category;

-- Trigger for JSON validation before insert
DELIMITER $$
CREATE TRIGGER normalize_specs_before_insert
BEFORE INSERT ON products
FOR EACH ROW
BEGIN
    -- Ensure specs is valid JSON. Note: JSON_VALID() exists in recent MariaDB versions.
    IF JSON_VALID(NEW.specs) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid JSON in specs column';
    END IF;
END$$
DELIMITER ;
