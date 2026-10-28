from flask import Flask, render_template, request, redirect, url_for, Response
import csv
import sqlite3

app = Flask(__name__)

# Create database
def create_database():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Expenses Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
create_database()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password)
        )

        conn.commit()
        conn.close()

        return "Registration Successful!"

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            return redirect(url_for("dashboard"))
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    conn.close()

    return render_template("dashboard.html", total=total)

@app.route("/add_expense", methods=["GET", "POST"])

def add_expense():

    if request.method == "POST":

        amount = request.form["amount"]
        category = request.form["category"]
        description = request.form["description"]
        date = request.form["date"]

        # Temporary user ID (we'll replace this after adding sessions)
        user_id = 1

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO expenses (user_id, amount, category, description, date)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, amount, category, description, date))

        conn.commit()
        conn.close()

        return "Expense Added Successfully!"

    return render_template("add_expense.html")

@app.route("/view_expenses")
def view_expenses():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()

    conn.close()

    return render_template("view_expenses.html", expenses=expenses)

@app.route("/logout")
def logout():
    return redirect(url_for("login"))

@app.route("/edit_expense/<int:id>", methods=["GET", "POST"])
def edit_expense(id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":

        amount = request.form["amount"]
        category = request.form["category"]
        description = request.form["description"]
        date = request.form["date"]

        cursor.execute("""
            UPDATE expenses
            SET amount=?, category=?, description=?, date=?
            WHERE id=?
        """, (amount, category, description, date, id))

        conn.commit()
        conn.close()

        return redirect(url_for("view_expenses"))

    cursor.execute("SELECT * FROM expenses WHERE id=?", (id,))
    expense = cursor.fetchone()

    conn.close()

    return render_template("edit_expense.html", expense=expense)

@app.route("/delete_expense/<int:id>")
def delete_expense(id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM expenses WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("view_expenses"))

@app.route("/export_csv")
def export_csv():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT amount, category, description, date
        FROM expenses
    """)

    expenses = cursor.fetchall()
    conn.close()

    def generate():
        yield "Amount,Category,Description,Date\n"
        for expense in expenses:
            yield f"{expense[0]},{expense[1]},{expense[2]},{expense[3]}\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=expenses.csv"
        }
    )

@app.route("/monthly_report")
def monthly_report():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT substr(date, 1, 7) AS month,
               SUM(amount) AS total
        FROM expenses
        GROUP BY month
        ORDER BY month
    """)

    report = cursor.fetchall()

    conn.close()

    return render_template("monthly_report.html", report=report)
if __name__ == "__main__":
    app.run(debug=True)