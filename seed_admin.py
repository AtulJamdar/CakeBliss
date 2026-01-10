import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "cake_bakery.db"

ADMIN_EMAIL = "admin"
ADMIN_PASSWORD = "admin@123"
ADMIN_ROLE = "admin"


def seed_admin():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if admin already exists
    cursor.execute(
        "SELECT id FROM users WHERE username = ?",
        (ADMIN_EMAIL,)
    )

    if cursor.fetchone():
        print("⚠️ Admin already exists. Skipping insert.")
        conn.close()
        return

    hashed_password = generate_password_hash(ADMIN_PASSWORD)

    cursor.execute("""
        INSERT INTO users (username, password, role)
        VALUES (?, ?, ?)
    """, (ADMIN_EMAIL, hashed_password, ADMIN_ROLE))

    conn.commit()
    conn.close()

    print("✅ Admin user created successfully")
    print(f"📧 Username: {ADMIN_EMAIL}")
    print(f"🔐 Password: {ADMIN_PASSWORD}")


if __name__ == "__main__":
    seed_admin()
