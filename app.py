

from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


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
    app.run(debug=True)
