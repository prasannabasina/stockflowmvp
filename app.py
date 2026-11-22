
from flask import Flask, render_template ,request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

import sqlite3

app = Flask(__name__)
app.secret_key = "stockflow_secret_key"


def get_db_connection():
    conn = sqlite3.connect("stockflow.db")
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


@app.route("/login")
def login():
    return render_template("login.html")



@app.route("/products")
def products():
    return render_template("products.html")
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/add-product")
def add_product():
    return render_template("add_products.html")

@app.route("/edit-product")
def edit_product():
    return render_template("edit_products.html")


if __name__ == "__main__":
    create_tables()
    app.run(debug=True)


