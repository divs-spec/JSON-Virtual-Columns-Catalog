import random, json, sys
from faker import Faker


fake = Faker()


GPUS = ['RTX 4070','RTX 4060','GTX 1660','Integrated','RTX 4080']
CATEGORIES = ['laptop','desktop','monitor','phone']
RAM_OPTIONS = [8,16,32,64]
SCREENS = [13.3,14.0,15.6,16.0,17.3]
BATTERY = [3000,4000,5000,6500]


N = 300000


with open("products_inserts.sql", "w") as f:
f.write("USE catalog;\n")
for i in range(N):
name = fake.word() + '-' + str(i)
category = random.choice(CATEGORIES)
price = round(random.uniform(200, 3000), 2)
ram = random.choice(RAM_OPTIONS)
gpu = random.choice(GPUS)
screen = round(random.choice(SCREENS),1)
battery = random.choice(BATTERY)


stmt = f"INSERT INTO products (name, category, price, specs) VALUES (\\n"
stmt += f" '{name}', '{category}', {price}, JSON_OBJECT('ram', {ram}, 'gpu', '{gpu}', 'screen_inches', {screen}, 'battery_mAh', {battery}));\\n"
f.write(stmt)


print("Generated products_inserts.sql with 300k rows")
