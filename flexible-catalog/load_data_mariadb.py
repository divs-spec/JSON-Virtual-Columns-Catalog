#!/usr/bin/env python3
"""
load_data_mariadb.py

Generates product rows and writes:
 - products_inserts_mariadb.sql  (batched INSERTs)
 - products_mariadb.csv           (CSV)
 
This writes both the 'specs' JSON column and the physical indexed columns:
 ram_gb, storage_gb, gpu, screen_size, battery_mah, cpu, brand
"""

import json
import random
import csv
from faker import Faker
from tqdm import tqdm
import os

fake = Faker()

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

def choose_or_none(lst):
    return random.choice(lst) if lst and random.random() > 0.05 else None

def generate_product(product_id, category):
    tpl = SPECS_BY_CATEGORY.get(category, SPECS_BY_CATEGORY['laptop'])
    specs = {}

    # Fill common spec keys if present in template
    for key, vals in tpl.items():
        if key == 'price_range':
            continue
        if isinstance(vals, list):
            # small chance to omit optional field (simulate sparse JSON)
            if random.random() < 0.02:
                continue
            specs[key] = random.choice(vals)

    name = f"{specs.get('brand','Generic')}-{category}-{product_id}"
    price_min, price_max = tpl['price_range']
    price = round(random.uniform(price_min, price_max), 2)

    # map to physical columns (some categories don't have all of them)
    ram = specs.get('ram')
    storage = specs.get('storage')
    gpu = specs.get('gpu')
    screen_size = specs.get('screen_size')
    battery = specs.get('battery_mah')
    cpu = specs.get('cpu')
    brand = specs.get('brand')

    return {
        'name': name,
        'category': category,
        'price': price,
        'specs': specs,      # dict; will be dumped as JSON
        'ram_gb': ram,
        'storage_gb': storage,
        'gpu': gpu,
        'screen_size': screen_size,
        'battery_mah': battery,
        'cpu': cpu,
        'brand': brand
    }

def sql_escape(s):
    if s is None:
        return 'NULL'
    # double single-quotes for SQL literal
    return "'" + str(s).replace("'", "''") + "'"

def generate_and_save(num_products=300000, batch_size=1000,
                      sql_filename='products_inserts_mariadb.sql',
                      csv_filename='products_mariadb.csv'):
    categories = list(SPECS_BY_CATEGORY.keys())

    # SQL file
    with open(sql_filename, 'w', encoding='utf-8') as sqlf:
        sqlf.write("USE catalog;\n")
        sqlf.write("SET foreign_key_checks = 0;\n")
        sqlf.write("TRUNCATE TABLE products;\n")
        sqlf.write("SET foreign_key_checks = 1;\n\n")

        batch = []
        for i in tqdm(range(1, num_products + 1)):
            category = random.choice(categories)
            p = generate_product(i, category)
            batch.append(p)

            if len(batch) >= batch_size:
                write_sql_batch(sqlf, batch)
                batch = []

        # final partial batch
        if batch:
            write_sql_batch(sqlf, batch)

    # CSV
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvf:
        writer = csv.writer(csvf)
        writer.writerow(['name','category','price','specs','ram_gb','storage_gb','gpu','screen_size','battery_mah','cpu','brand'])
        for i in tqdm(range(1, num_products + 1)):
            category = random.choice(categories)
            p = generate_product(i, category)
            writer.writerow([
                p['name'],
                p['category'],
                p['price'],
                json.dumps(p['specs'], ensure_ascii=False),
                p['ram_gb'] if p['ram_gb'] is not None else '',
                p['storage_gb'] if p['storage_gb'] is not None else '',
                p['gpu'] or '',
                p['screen_size'] if p['screen_size'] is not None else '',
                p['battery_mah'] if p['battery_mah'] is not None else '',
                p['cpu'] or '',
                p['brand'] or ''
            ])

    print(f"SQL saved to: {sql_filename}")
    print(f"CSV saved to: {csv_filename}")

def write_sql_batch(fh, batch):
    # columns: name, category, price, specs, ram_gb, storage_gb, gpu, screen_size, battery_mah, cpu, brand
    fh.write("INSERT INTO products (name, category, price, specs, ram_gb, storage_gb, gpu, screen_size, battery_mah, cpu, brand) VALUES\n")
    vals = []
    for p in batch:
        specs_json = json.dumps(p['specs'], ensure_ascii=False)
        name_sql = sql_escape(p['name'])
        cat_sql = sql_escape(p['category'])
        price_sql = str(p['price'])
        specs_sql = sql_escape(specs_json)
        ram_sql = str(p['ram_gb']) if p['ram_gb'] is not None else 'NULL'
        storage_sql = str(p['storage_gb']) if p['storage_gb'] is not None else 'NULL'
        gpu_sql = sql_escape(p['gpu']) if p['gpu'] is not None else 'NULL'
        screen_sql = str(p['screen_size']) if p['screen_size'] is not None else 'NULL'
        batt_sql = str(p['battery_mah']) if p['battery_mah'] is not None else 'NULL'
        cpu_sql = sql_escape(p['cpu']) if p['cpu'] is not None else 'NULL'
        brand_sql = sql_escape(p['brand']) if p['brand'] is not None else 'NULL'

        vals.append(f"({name_sql},{cat_sql},{price_sql},{specs_sql},{ram_sql},{storage_sql},{gpu_sql},{screen_sql},{batt_sql},{cpu_sql},{brand_sql})")

    fh.write(",\n".join(vals))
    fh.write(";\n\n")

if __name__ == "__main__":
    # Quick sanity default: generate 50k products for local testing if not changed
    NUM = int(os.getenv('NUM_PRODUCTS', '50000'))
    generate_and_save(num_products=NUM, batch_size=1000)
