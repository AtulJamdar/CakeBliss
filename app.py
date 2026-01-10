from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import functools

app = Flask(__name__)
app.secret_key = "cake_bakery_secret_123"
DATABASE = "cake_bakery.db"

# =========================
# DATABASE HELPERS
# =========================
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    # Users Table
    db.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user'
    )""")
    # Cakes Table
    db.execute("""CREATE TABLE IF NOT EXISTS cakes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT,
        image TEXT,
        category TEXT
    )""")
    # Orders Table
    db.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        cake_name TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    # Create default admin if not exists
    admin_exists = db.execute("SELECT * FROM users WHERE role='admin'").fetchone()
    if not admin_exists:
        db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   ("admin", generate_password_hash("admin123"), "admin"))
    db.commit()

# =========================
# STATIC PAGES
# =========================



@app.route("/services")
def services():
    # This renders the services.html template
    return render_template("services.html")



# =========================
# AUTH DECORATORS
# =========================
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Admin access required.")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# =========================
# ROUTES
# =========================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/shop")
def shop():
    db = get_db()
    category = request.args.get('category')
    if category:
        cakes = db.execute("SELECT * FROM cakes WHERE category=?", (category,)).fetchall()
    else:
        cakes = db.execute("SELECT * FROM cakes").fetchall()
    return render_template("shop.html", cakes=cakes)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            db.commit()
            flash("Registration successful! Please login.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists.")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (request.form['username'],)).fetchone()
        if user and check_password_hash(user['password'], request.form['password']):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['cart'] = []
            return redirect(url_for('admin_dashboard' if user['role'] == 'admin' else 'index'))
        flash("Invalid credentials.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

# =========================
# CART & CHECKOUT
# =========================

@app.route("/add_to_cart/<int:cake_id>")
@login_required
def add_to_cart(cake_id):
    db = get_db()
    cake = db.execute("SELECT * FROM cakes WHERE id=?", (cake_id,)).fetchone()
    if cake:
        cart = session.get('cart', [])
        cart.append({'id': cake['id'], 'name': cake['name'], 'price': cake['price'], 'image': cake['image'], 'qty': 1})
        session['cart'] = cart
        flash(f"{cake['name']} added to cart!")
    return redirect(url_for('shop'))

@app.route("/cart")
@login_required
def cart():
    cart_items = session.get('cart', [])
    total = sum(item['price'] for item in cart_items)
    return render_template("cart.html", cart=cart_items, total=total)

@app.route("/remove_from_cart/<int:index>")
def remove_from_cart(index):
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session['cart'] = cart
    return redirect(url_for('cart'))

@app.route("/checkout")
@login_required
def checkout():
    db = get_db()
    cart = session.get('cart', [])
    for item in cart:
        db.execute("INSERT INTO orders (user_id, cake_name) VALUES (?, ?)",
                   (session['user_id'], item['name']))
    db.commit()
    session['cart'] = []
    flash("Order placed successfully!")
    return redirect(url_for('user_dashboard'))

# =========================
# DASHBOARDS
# =========================

@app.route("/user/dashboard")
@login_required
def user_dashboard():
    db = get_db()
    orders = db.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC",
                        (session['user_id'],)).fetchall()
    return render_template("dashboard_user.html", orders=orders)

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    db = get_db()

    # 1. Fetch Orders, Users, and Cakes
    orders = db.execute("""
        SELECT orders.*, users.username
        FROM orders
        JOIN users ON orders.user_id = users.id
        ORDER BY created_at DESC
    """).fetchall()
    cakes = db.execute("SELECT * FROM cakes").fetchall()
    users = db.execute("SELECT * FROM users").fetchall()

    # 2. Fetch Analytics Data
    status_data = db.execute("SELECT status, COUNT(*) as count FROM orders GROUP BY status").fetchall()
    labels = [row['status'] for row in status_data]
    values = [row['count'] for row in status_data]

    cake_sales = db.execute("SELECT cake_name, COUNT(*) as count FROM orders GROUP BY cake_name").fetchall()
    cakes_json = [dict(row) for row in cake_sales]

    return render_template(
        "dashboard_admin.html",
        orders=orders,
        cakes=cakes,
        users=users,
        labels=labels,
        values=values,
        cakes_json=cakes_json
    )

@app.route("/admin/analytics")
@admin_required
def analytics():
    db = get_db()
    # Data for Order Status Distribution
    status_data = db.execute("SELECT status, COUNT(*) as count FROM orders GROUP BY status").fetchall()
    labels = [row['status'] for row in status_data]
    values = [row['count'] for row in status_data]

    # Data for Cake Sales
    cake_sales = db.execute("SELECT cake_name, COUNT(*) as count FROM orders GROUP BY cake_name").fetchall()
    cakes_json = [dict(row) for row in cake_sales]

    return render_template("analytics.html", labels=labels, values=values, cakes=cakes_json)

# =========================
# ADMIN ACTIONS
# =========================

@app.route("/admin/add_cake", methods=["GET", "POST"])
@admin_required
def admin_add_cake():
    if request.method == "POST":
        db = get_db()
        # Use .get() to avoid BadRequestKeyError
        name = request.form.get('name')
        price = request.form.get('price')
        desc = request.form.get('description')
        img = request.form.get('image')
        cat = request.form.get('category')

        db.execute("INSERT INTO cakes (name, price, description, image, category) VALUES (?, ?, ?, ?, ?)",
                   (name, price, desc, img, cat))
        db.commit()
        flash("New cake added!")
        return redirect(url_for('admin_dashboard'))
    return render_template("admin_add_cake.html")

@app.route("/admin/edit_cake/<int:cake_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_cake(cake_id):
    db = get_db()
    if request.method == "POST":
        db.execute("UPDATE cakes SET name=?, price=?, description=?, image=?, category=? WHERE id=?",
                   (request.form['name'], request.form['price'], request.form['description'],
                    request.form['image'], request.form['category'], cake_id))
        db.commit()
        flash("Cake updated successfully!")
        return redirect(url_for('admin_dashboard'))

    cake = db.execute("SELECT * FROM cakes WHERE id=?", (cake_id,)).fetchone()
    return render_template("admin_edit_cake.html", cake=cake)

@app.route("/admin/update_order/<int:order_id>", methods=["POST"])
@admin_required
def update_order(order_id):
    db = get_db()
    db.execute("UPDATE orders SET status=? WHERE id=?", (request.form['status'], order_id))
    db.commit()
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/delete_cake/<int:cake_id>")
@admin_required
def admin_delete_cake(cake_id):
    db = get_db()
    db.execute("DELETE FROM cakes WHERE id=?", (cake_id,))
    db.commit()
    flash("Cake deleted successfully!")
    return redirect(url_for('admin_dashboard'))

# =========================
# ADMIN USER MANAGEMENT
# =========================

@app.route("/admin/update_user_role/<int:user_id>", methods=["POST"])
@admin_required
def update_user_role(user_id):
    db = get_db()
    new_role = request.form.get('role')
    db.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
    db.commit()
    flash("User role updated!")
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    db = get_db()
    # Prevent admin from deleting themselves
    if user_id == session.get('user_id'):
        flash("You cannot delete your own account!")
    else:
        db.execute("DELETE FROM users WHERE id=?", (user_id,))
        db.commit()
        flash("User deleted.")
    return redirect(url_for('admin_dashboard'))

@app.route("/about")
def about(): return render_template("about.html")

@app.route("/contact")
def contact(): return render_template("contact.html")

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)