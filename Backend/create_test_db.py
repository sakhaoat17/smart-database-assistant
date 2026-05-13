import sqlite3

# Connect to SQLite database (it will create the database file if it doesn't exist)
conn = sqlite3.connect('northwind.db')
cursor = conn.cursor()

# Create a simple products table
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL
)
''')

# Insert sample data
sample_data = [
    (1, 'Laptop', 'Electronics', 999.99, 50),
    (2, 'Mouse', 'Electronics', 29.99, 100),
    (3, 'Keyboard', 'Electronics', 79.99, 75),
    (4, 'Monitor', 'Electronics', 299.99, 30),
    (5, 'Desk Chair', 'Furniture', 199.99, 25),
    (6, 'Desk', 'Furniture', 399.99, 15),
    (7, 'Coffee Mug', 'Kitchen', 12.99, 200),
    (8, 'Water Bottle', 'Kitchen', 19.99, 150)
]

cursor.executemany('INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?, ?)', sample_data)

# Create customers table
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    city TEXT NOT NULL
)
''')

customer_data = [
    (1, 'John Doe', 'john@email.com', 'New York'),
    (2, 'Jane Smith', 'jane@email.com', 'Los Angeles'),
    (3, 'Bob Johnson', 'bob@email.com', 'Chicago'),
    (4, 'Alice Brown', 'alice@email.com', 'Houston')
]

cursor.executemany('INSERT OR REPLACE INTO customers VALUES (?, ?, ?, ?)', customer_data)

# Create orders table
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    order_date TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
)
''')

order_data = [
    (1, 1, 1, 1, '2024-01-15'),
    (2, 1, 2, 2, '2024-01-15'),
    (3, 2, 3, 1, '2024-01-16'),
    (4, 3, 4, 1, '2024-01-17'),
    (5, 4, 5, 1, '2024-01-18'),
    (6, 2, 7, 3, '2024-01-19'),
    (7, 3, 8, 2, '2024-01-20')
]

cursor.executemany('INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?, ?)', order_data)

conn.commit()
conn.close()

print("Test database created successfully!")
print("Tables: products, customers, orders")
print("You can now test with queries like:")
print("- 'Show me all products'")
print("- 'What are the sales by category?'")
print("- 'Show me customer orders'")
