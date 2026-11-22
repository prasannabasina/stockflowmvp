
from flask import Flask, render_template ,request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

import sqlite3

app = Flask(__name__)
app.secret_key = "stockflow_secret_key"
def get_db_connection():
    conn = sqlite3.connect("stockflow.db", timeout=20)
    return conn
def create_tables():
    conn = get_db_connection()

    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)

  
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            organization_id INTEGER,
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        )
    """)

    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            sku TEXT NOT NULL,
            description TEXT,
            quantity INTEGER NOT NULL,
            cost_price REAL,
            selling_price REAL,
            low_stock_threshold INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (organization_id) REFERENCES organizations(id),
            UNIQUE (organization_id, sku)
        )
    """)

    conn.commit()
    conn.close()

# Signup page
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


# Signup functionality
@app.route("/signup", methods=["POST"])
def signup():
    email = request.form["email"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]
    organization_name = request.form["organization_name"]

    if password != confirm_password:
        return "Passwords do not match"

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()

    cursor = conn.execute(
        "INSERT INTO organizations (name) VALUES (?)",
        (organization_name,)
    )

    organization_id = cursor.lastrowid

    conn.execute(
        "INSERT INTO users (email, password, organization_id) VALUES (?, ?, ?)",
        (email, hashed_password, organization_id)
    )

    conn.commit()
    conn.close()

    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["organization_id"] = user[3]

            return redirect("/dashboard")

        return "Invalid email or password"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "organization_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    total_products = conn.execute("""
        SELECT COUNT(*) FROM products
        WHERE organization_id = ?
    """, (session["organization_id"],)).fetchone()[0]

    total_quantity = conn.execute("""
        SELECT SUM(quantity) FROM products
        WHERE organization_id = ?
    """, (session["organization_id"],)).fetchone()[0]

    if total_quantity is None:
        total_quantity = 0

    low_stock_products = conn.execute("""
        SELECT name, quantity, low_stock_threshold
        FROM products
        WHERE organization_id = ?
    """, (session["organization_id"],)).fetchall()

    conn.close()

    low_stock = []

    for product in low_stock_products:
        threshold = product[2] if product[2] is not None else 5

        if product[1] <= threshold:
            low_stock.append(product)

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_quantity=total_quantity,
        low_stock=low_stock
    )
@app.route("/products")
def products():
    if "organization_id" not in session:
        return redirect("/login")

    search = request.args.get("search", "")

    conn = get_db_connection()

    products = conn.execute("""
        SELECT * FROM products
        WHERE organization_id = ?
        AND (name LIKE ? OR sku LIKE ?)
    """, (
        session["organization_id"],
        "%" + search + "%",
        "%" + search + "%"
    )).fetchall()

    conn.close()

    return render_template("products.html", products=products)

@app.route("/add-product", methods=["GET", "POST"])
def add_product():
    if "organization_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        name = request.form["name"]
        sku = request.form["sku"]
        description = request.form["description"]
        quantity = int(request.form["quantity"])

        cost_price = request.form.get("cost_price") or None
        selling_price = request.form.get("selling_price") or None

        threshold = request.form.get("low_stock_threshold")

        if threshold:
            threshold = int(threshold)
        else:
            threshold = None

        conn = get_db_connection()

        try:
            conn.execute("""
                INSERT INTO products
                (organization_id, name, sku, description, quantity,
                 cost_price, selling_price, low_stock_threshold)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session["organization_id"],
                name,
                sku,
                description,
                quantity,
                cost_price,
                selling_price,
                threshold
            ))

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "This SKU already exists in your organization"

        conn.close()

        return redirect("/products")

    return render_template("add_products.html")


@app.route("/edit-product", methods=["GET", "POST"])
def edit_product():

    if "organization_id" not in session:
        return redirect("/login")

    product_id = request.args.get("id")

    conn = get_db_connection()

    if request.method == "POST":

        name = request.form["name"]
        sku = request.form["sku"]
        description = request.form["description"]
        quantity = int(request.form["quantity"])

        cost_price = request.form.get("cost_price") or None
        selling_price = request.form.get("selling_price") or None

        threshold = request.form.get("low_stock_threshold")
        if threshold:
            threshold = int(threshold)
        else:
            threshold = None

        conn.execute("""
            UPDATE products
            SET name = ?, sku = ?, description = ?, quantity = ?,
                cost_price = ?, selling_price = ?, low_stock_threshold = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND organization_id = ?
        """, (
            name, sku, description, quantity,
            cost_price, selling_price, threshold,
            product_id, session["organization_id"]
        ))

        conn.commit()
        conn.close()

        return redirect("/products")

    product = conn.execute("""
        SELECT * FROM products
        WHERE id = ? AND organization_id = ?
    """, (product_id, session["organization_id"])).fetchone()

    conn.close()

    if product is None:
        return "Product not found"

    return render_template("edit_products.html", product=product)
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):

    if "organization_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM products
        WHERE id = ? AND organization_id = ?
    """, (product_id, session["organization_id"]))

    conn.commit()
    conn.close()

    return redirect("/products")
if __name__ == "__main__":
    create_tables()
    app.run(debug=True)


