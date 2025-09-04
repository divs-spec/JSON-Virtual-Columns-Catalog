import random
import csv
from faker import Faker
from collections import defaultdict

fake = Faker()

NUM_ROWS = 300_000
CATEGORIES = ["laptop", "desktop", "tablet", "phone"]

# Specs ranges
RAM_OPTIONS = [4, 8, 16, 32, 64]
GPU_OPTIONS = ["RTX 3050", "RTX 3060", "RTX 4070", "RTX 4090", "Integrated"]
SCREEN_OPTIONS = [13.3, 14.0, 15.6, 17.3, 27.0]
BATTERY_OPTIONS = [4000, 5000, 6000, 7000, 8000]

# Output files
SQL_FILE = "products_inserts.sql"
CSV_FILE = "products.csv"

def gen_row(i):
    category = random.choice(CATEGORIES)
    name = f"{category}-{i}"
    price = round(random.uniform(200, 3000), 2)
    ram = random.choice(RAM_OPTIONS)
    gpu = random.choice(GPU_OPTIONS)
    screen = random.choice(SCREEN_OPTIONS)
    battery = random.choice(BATTERY_OPTIONS)

    specs = {
        "ram": ram,
        "gpu": gpu,
        "screen_inches": screen,
        "battery": battery
    }

    return (name, category, price, specs)

def generate_sql(rows):
    with open(SQL_FILE, "w") as f:
        f.write("USE catalog;\n")
        f.write("INSERT INTO products (name, category, price, specs) VALUES\n")
        values = []
        for (name, category, price, specs) in rows:
            values.append(f"(\"{name}\", \"{category}\", {price}, '{specs}')")
        f.write(",\n".join(values) + ";\n")
    print(f"[OK] SQL insert script written to {SQL_FILE}")

def generate_csv(rows):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "category", "price", "specs"])  # header
        for (name, category, price, specs) in rows:
            writer.writerow([name, category, price, str(specs)])
    print(f"[OK] CSV file written to {CSV_FILE}")

def log_stats(rows):
    stats = defaultdict(list)
    for _, cat, _, specs in rows:
        stats[cat].append(specs["ram"])
    print("=== Stats ===")
    for cat, rams in stats.items():
        avg_ram = sum(rams) / len(rams)
        print(f"{cat}: {len(rams)} rows, avg RAM = {avg_ram:.1f} GB")

if __name__ == "__main__":
    rows = [gen_row(i) for i in range(1, NUM_ROWS + 1)]
    generate_sql(rows)
    generate_csv(rows)
    log_stats(rows)

    print(\"\\nImport CSV with:\")
    print(f\"LOAD DATA INFILE '/path/to/{CSV_FILE}' INTO TABLE products \\\")\n    FIELDS TERMINATED BY ',' ENCLOSED BY '\"' \\\n    LINES TERMINATED BY '\\n' IGNORE 1 ROWS \\\n    (name, category, price, specs);\")\n```\n\n---\n\n## 🚀 How to use\n\n1. Generate the data:\n   ```bash\n   python3 load_data.py\n   ```\n   → produces `products_inserts.sql` and `products.csv`\n\n2. **Fast import using CSV** (recommended):\n   ```sql\n   LOAD DATA INFILE '/absolute/path/products.csv'\n   INTO TABLE products\n   FIELDS TERMINATED BY ',' ENCLOSED BY '\"'\n   LINES TERMINATED BY '\\n'\n   IGNORE 1 ROWS\n   (name, category, price, specs);\n   ```\n\n   ⚠️ Make sure MySQL has permissions for the file (check `secure_file_priv`).\n\n3. **Slower SQL insert method**:\n   ```bash\n   mysql -h127.0.0.1 -P3306 -u root -proot < products_inserts.sql\n   ```\n\n---\n\n✅ This script gives you both worlds: **fast CSV import** for huge datasets and **SQL inserts** for portability. Plus, you get summary stats for quick sanity checks.\n\n---\n\nWant me to also add a **ready-made SQL script for `LOAD DATA INFILE`** (so you don’t have to type it manually) that works after `load_data.py` runs?
