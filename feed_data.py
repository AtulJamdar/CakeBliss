import sqlite3

DB_NAME = "cake_bakery.db"

cakes_data = [
    # Chocolate
    ("Dark Chocolate Cake", 499, "Rich dark chocolate layered cake",
     "https://images.unsplash.com/photo-1601979031925-424e53b6caaa", "Chocolate"),
    ("Chocolate Truffle", 599, "Smooth chocolate truffle delight",
     "https://images.unsplash.com/photo-1578985545062-69928b1d9587", "Chocolate"),
    ("Chocolate Fudge", 549, "Soft chocolate fudge cake",
     "https://images.unsplash.com/photo-1605475129364-4aebc56cbb92", "Chocolate"),

    # Birthday
    ("Birthday Sprinkles Cake", 699, "Colorful cake perfect for birthdays",
     "https://images.unsplash.com/photo-1565958011703-44f9829ba187", "Birthday"),
    ("Kids Cartoon Cake", 799, "Fun cartoon themed birthday cake",
     "https://images.unsplash.com/photo-1586985289688-ca3cf47d3e6e", "Birthday"),
    ("Vanilla Celebration Cake", 649, "Classic vanilla birthday cake",
     "https://images.unsplash.com/photo-1542826438-bd32f43d626f", "Birthday"),

    # Wedding
    ("Classic Wedding Cake", 2499, "Elegant multi-layer wedding cake",
     "https://images.unsplash.com/photo-1525253086316-d0c936c814f8", "Wedding"),
    ("Royal White Wedding Cake", 2999, "Premium white wedding cake",
     "https://images.unsplash.com/photo-1546039907-7fa05f864c02", "Wedding"),
    ("Floral Wedding Cake", 2799, "Wedding cake with floral design",
     "https://images.unsplash.com/photo-1607083207186-3d4f2f62d04f", "Wedding"),

    # Fruit
    ("Fresh Fruit Cake", 599, "Seasonal fresh fruit cake",
     "https://images.unsplash.com/photo-1606313564200-e75d5e30476c", "Fruit"),
    ("Strawberry Cream Cake", 649, "Strawberry layered cream cake",
     "https://images.unsplash.com/photo-1588195538326-c5b1e9f80a1b", "Fruit"),

    # Special
    ("Red Velvet Cake", 699, "Classic red velvet with cream cheese",
     "https://images.unsplash.com/photo-1614707267537-b85aaf00c4b7", "Special"),
    ("Blueberry Cheesecake", 749, "Creamy blueberry cheesecake",
     "https://images.unsplash.com/photo-1562440499-64c9a111f713", "Special"),
]

def seed_cakes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for cake in cakes_data:
        cursor.execute("""
            INSERT INTO cakes (name, price, description, image, category)
            VALUES (?, ?, ?, ?, ?)
        """, cake)

    conn.commit()
    conn.close()
    print("✅ Cakes data inserted successfully")

if __name__ == "__main__":
    seed_cakes()
