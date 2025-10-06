#!/usr/bin/env python3
import json
import random
import csv
from faker import Faker
from datetime import datetime
import mysql.connector
from tqdm import tqdm
import os

fake = Faker()

# Product specifications by category
SPECS_BY_CATEGORY = {
    'laptop': {
        'ram': [8, 16, 32, 64],
        'storage': [256, 512, 1024, 2048],
        'gpu': ['Intel Iris', 'RTX 3050', 'RTX 3060', 'RTX 4070', 'RTX 4080', 'AMD Radeon'],
        'screen_size': [13.3, 14.0, 15.6, 16.0, 17.3],
        'cpu': ['Intel i5', 'Intel i7', 'Intel i9', 'AMD Ryzen 5', 'AMD Ryzen 7', 'AMD Ryzen 9'],
        'brand': ['Dell', 'HP', 'Lenovo', 'Apple', 'Asus', 'MSI', 'Acer'],
        'price_range': (500, 3000)
    },
    'phone': {
        'ram': [4, 6, 8, 12, 16],
        'storage': [64, 128, 256, 512, 1024],
        'screen_size': [5.5, 6.1, 6.4, 6.7, 6.9],
        'battery_mah': [3000, 4000, 4500, 5000, 6000],
        'brand': ['Apple', 'Samsung', 'Google', 'OnePlus', 'Xiaomi', 'Oppo'],
        'price_range': (200, 1500)
    },
    'tablet': {
        'ram': [4, 6, 8, 12, 16],
        'storage': [64, 128, 256, 512],
        'screen_size': [8.0, 10.1, 11.0, 12.9],
        'battery_mah': [5000, 7000, 8000, 10000],
        'brand': ['Apple', 'Samsung', 'Microsoft', 'Amazon', 'Lenovo'],
        'price_range': (150, 1200)
    },
    'desktop': {
        'ram': [8, 16, 32, 64, 128],
        'storage': [512, 1024, 2048, 4096],
        'gpu': ['RTX 3060', 'RTX 3070', 'RTX 4070', 'RTX 4080', 'RTX 4090', 'AMD RX 7900'],
        'cpu': ['Intel i5', 'Intel i7', 'Intel i9', 'AMD Ryzen 5', 'AMD Ryzen 7', 'AMD Ryzen 9'],
        'brand': ['Dell', 'HP', 'Lenovo', 'Custom Build', 'Alienware'],
        'price_range': (600, 5000)
    }
}

def generate_product(product_id, category):
    """Generate a single product with specifications"""
    specs_template = SPECS_BY_CATEGORY.get(category, SPECS_BY_CATEGORY['laptop'])
    
    specs = {}
    for key, values in specs_template.items():
        if key != 'price_range':
            if isinstance(values, list):
                specs[key] = random.choice(values)
    
    name = f"{specs.get('brand', 'Generic')}-{category}-{product_id}"
    price_min, price_max = specs_template['price_range']
    price = round(random.uniform(price_min, price_max), 2)
    
    return {
        'name': name,
        'category': category,
        'price': price,
        'specs': json.dumps(specs)
    }

def generate_data(num_products=300000):
    """Generate product data"""
    print(f"Generating {num_products} products...")
    
    categories = list(SPECS_BY_CATEGORY.keys())
    products = []
    
    for i in tqdm(range(1, num_products + 1)):
        category = random.choice(categories)
        product = generate_product(i, category)
        products.append(product)
    
    return products

def save_to_sql(products, filename='products_inserts.sql'):
    """Save products as SQL insert statements"""
    print(f"Saving to {filename}...")
    
    with open(filename, 'w') as f:
        f.write("USE catalog;\n")
        f.write("SET foreign_key_checks = 0;\n")
        f.write("TRUNCATE TABLE products;\n")
        f.write("SET foreign_key_checks = 1;\n\n")
        
        # Batch inserts for better performance
        batch_size = 1000
        for i in range(0, len(products), batch_size):
            batch = products[i:i+batch_size]
            f.write("INSERT INTO products (name, category, price, specs) VALUES\n")
            
            values = []
            for product in batch:
                specs_escaped = product['specs'].replace("'", "\\'")
                values.append(f"('{product['name']}', '{product['category']}', {product['price']}, '{specs_escaped}')")
            
            f.write(",\n".join(values))
            f.write(";\n\n")
    
    print(f"SQL file saved: {filename}")

def save_to_csv(products, filename='products.csv'):
    """Save products as CSV for bulk loading"""
    print(f"Saving to {filename}...")
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'category', 'price', 'specs'])
        
        for product in products:
            writer.writerow([
                product['name'],
                product['category'],
                product['price'],
                product['specs']
            ])
    
    print(f"CSV file saved: {filename}")

def load_to_db(products):
    """Load products directly to database"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', 3306),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASS', 'root'),
            database=os.getenv('DB_NAME', 'catalog')
        )
        cursor = conn.cursor()
        
        print("Loading to database...")
        cursor.execute("TRUNCATE TABLE products")
        
        insert_query = """
        INSERT INTO products (name, category, price, specs) 
        VALUES (%s, %s, %s, %s)
        """
        
        batch_size = 5000
        for i in tqdm(range(0, len(products), batch_size)):
            batch = products[i:i+batch_size]
            data = [(p['name'], p['category'], p['price'], p['specs']) for p in batch]
            cursor.executemany(insert_query, data)
            conn.commit()
        
        print("Data loaded successfully!")
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        print("Falling back to SQL/CSV file generation...")

if __name__ == "__main__":
    # Generate data
    products = generate_data(300000)
    
    # Save to files
    save_to_sql(products)
    save_to_csv(products)
    
    # Try direct DB load
    # load_to_db(products)
    
    print("\n✅ Data generation complete!")
    print("Next steps:")
    print("1. Load SQL: mysql -h127.0.0.1 -u root -p < products_inserts.sql")
    print("2. Or load CSV: LOAD DATA INFILE 'products.csv' INTO TABLE products...")
