# Complete Expense Tracker Project with Flask, MySQL, and Enhanced GUI

from flask import Flask, render_template, request, redirect, session, url_for, Response, flash # type: ignore
import mysql.connector # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore
import matplotlib.pyplot as plt # type: ignore
import io
import csv  # Import the csv module for generating CSV files

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "secretkey"

# MySQL Database Configuration
db = mysql.connector.connect(
    host="localhost",
    user="root",  # Replace with your MySQL username
    password="Lalit@12911",  # Replace with your MySQL password
    database="expense_tracker",
    connection_timeout=600
)
cursor = db.cursor(dictionary=True)

# Routes

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':                         #If the request is a POST, it means the user submitted the registration form.The server now processes the submitted data.(here accessing mean data is processed by the server further store it on the database)
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        query = "INSERT INTO users (username, email, hashed_password) VALUES (%s, %s, %s)"   #%s placeholders are used to safely insert user-provided values, preventing SQL Injection attacks.
        cursor.execute(query, (username, email, password))
        db.commit()                                      #Finalizes the insertion into the database by committing the transaction.
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')              #The user sees the registration form (an HTML page) in their browser.

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['hashed_password'], password):
            session['user_id'] = user['id']
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials. Try again.", "error")

    return render_template('login.html')

# User Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    query = "SELECT * FROM expenses WHERE user_id = %s ORDER BY date DESC"
    cursor.execute(query, (user_id,))
    expenses = cursor.fetchall()

    query_total = "SELECT SUM(amount) AS total FROM expenses WHERE user_id = %s"
    cursor.execute(query_total, (user_id,))
    total_expenses = cursor.fetchone()['total'] or 0

    return render_template('dashboard.html', expenses=expenses, total_expenses=total_expenses)



# Add Expense
@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        category = request.form['category']
        amount = request.form['amount']
        description = request.form['description']
        date = request.form['date']
        user_id = session['user_id']

        query = "INSERT INTO expenses (user_id, date, category, amount, description) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (user_id, date, category, amount, description))
        db.commit()
        flash("Expense added successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_expense.html')




# Export Expense Data as CSV
@app.route('/export_csv')
def export_csv():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    query = "SELECT date, category, amount, description FROM expenses WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    expenses = cursor.fetchall()

    # Generate CSV response
    output = io.StringIO()
    writer = csv.writer(output)

    # Write the header row
    writer.writerow(['Date', 'Category', 'Amount', 'Description'])

    # Write the expense data
    for expense in expenses:
        writer.writerow([expense['date'], expense['category'], expense['amount'], expense['description']])

    # Set the response for file download
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=expenses.csv'
    return response


# Spending Analytics

# @app.route('/analytics')
# def analytics():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     user_id = session['user_id']
#     query = "SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = %s GROUP BY category"
#     cursor.execute(query, (user_id,))
#     data = cursor.fetchall()  # Example: [{'category': 'Food', 'total': 150}, {'category': 'Travel', 'total': 300}]

#     return render_template('analytics.html', analytics_data=data)

@app.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    query = "SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = %s GROUP BY category"
    cursor.execute(query, (user_id,))
    data = cursor.fetchall()

    categories = [item['category'] for item in data]
    totals = [item['total'] for item in data]

    plt.figure(figsize=(8, 6))
    plt.bar(categories, totals, color='skyblue')
    plt.title('Spending by Category')
    plt.xlabel('Category')
    plt.ylabel('Amount')

    img = io.BytesIO()          #img = io.BytesIO(): Initializes an in-memory binary stream (BytesIO) to hold the image data.

    plt.savefig(img, format='png')
    img.seek(0)

    return Response(img.getvalue(), mimetype='image/png')

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
