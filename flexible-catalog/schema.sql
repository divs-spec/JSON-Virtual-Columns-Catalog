DROP DATABASE IF EXISTS catalog;
CREATE DATABASE catalog;
USE catalog;


CREATE TABLE products (
id BIGINT AUTO_INCREMENT PRIMARY KEY,
name VARCHAR(255) NOT NULL,
category VARCHAR(100) NOT NULL,
price DECIMAL(12,2) NOT NULL,
specs JSON NOT NULL,


ram_gb INT AS (JSON_UNQUOTE(JSON_EXTRACT(specs, '$.ram'))) STORED,
gpu VARCHAR(100) AS (JSON_UNQUOTE(JSON_EXTRACT(specs, '$.gpu'))) STORED,
screen_in DECIMAL(4,2) AS (JSON_UNQUOTE(JSON_EXTRACT(specs, '$.screen_inches'))) STORED,
battery_mah INT AS (JSON_UNQUOTE(JSON_EXTRACT(specs, '$.battery_mAh'))) STORED,


INDEX idx_category_price (category, price),
INDEX idx_ram_gb (ram_gb),
INDEX idx_gpu (gpu),
INDEX idx_screen_in (screen_in)
) ENGINE=InnoDB;
