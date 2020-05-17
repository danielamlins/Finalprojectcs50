import os

from flask import Flask, session, render_template, request, redirect
from flask import session as login_session
from flask_session import Session
from tempfile import mkdtemp
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

# Start the app
app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Make sure the user provided a valid username, password and matching password confirmation
        if not request.form.get("conf_password"):
            return render_template("register.html", no_confir_password='True')
        elif request.form.get("conf_password") != request.form.get("password"):
            return render_template("register.html", no_confir_password='True')

        # Make sure the username is available
        username = request.form.get("username")
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": username}).fetchone()
        if rows:
            return render_template("register.html", warning='not available')

        # Register the user
        password = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hashcode) VALUES (:username, :password)", 
                   {"username": username, "password": password})

        # Initialize tables
        user_info = db.execute("SELECT * FROM users WHERE username = :username",
                               {"username": username}).fetchone()
        id = user_info["id"]
        db.execute("INSERT INTO income (user_id, item, value) VALUES (:user, 'Salary', '0')",
                   {"user": id})
        db.execute("INSERT INTO monthly (user_id, item, fixed, expected, spent, available) VALUES (:user, 'Rent', '0', '0','0','0')",
                   {"user": id})    
        db.execute("INSERT INTO daily (user_id, item, fixed, expected, spent, available) VALUES (:user, 'Groceries', '0', '0','0','0')",
                   {"user": id})
        db.execute("INSERT INTO savings (user_id, item, fixed, expected, saved, available) VALUES (:user, 'Emergency', '0', '0','0','0')",
                   {"user": id})              
        db.commit()
        return render_template("login.html", warning='success')

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Checking for an existing username
        username = request.form.get("username")
        row = db.execute("SELECT * FROM users WHERE username = :username",
                         {"username": username}).fetchone()

        print(f"row = {row}")

        # Check if the username exists.
        if row == None:
            return render_template("login.html", warning='wrong_password', message="Invalid username.")

        # Check if the password is correct
        if not check_password_hash(row["hashcode"], request.form.get("password")):
            return render_template("login.html", warning='wrong_password', message="Wrong username and/or password")

        # Begin session and redirect
        session["user_id"] = row[0]

        login_session['username'] = row[1]
        print(f"login session {login_session}")

        return redirect("/app")

    else:
        return render_template("login.html")


@app.route("/app")
@login_required
def index():
    # Determine user
    user = login_session['user_id']
    
    # Select data from all the tables to be passd in into the "Overview" page
    income = db.execute("SELECT * FROM income WHERE user_id=:user",
                        {"user": user})    
    budget_monthly = db.execute("SELECT * FROM monthly WHERE user_id=:user",
                                {"user": user})
    budget_daily = db.execute("SELECT * FROM daily WHERE user_id=:user",
                              {"user": user})
    savings = db.execute("SELECT * FROM savings WHERE user_id=:user",
                         {"user": user})
    # Redirect
    return render_template("index.html", income=income, budget_daily=budget_daily, budget_monthly=budget_monthly, savings=savings)


@app.route("/logout")
@login_required
def logout():
    # Clear Session and return to the homepage
    session.clear()
    return redirect("/")


@app.route("/set", methods=["GET", "POST"])
@login_required
def set():
    if request.method == "POST":
        # Determine user and chosen table
        table = request.form.get("chosen_table")
        user = login_session['user_id']
                
        # Set return message
        message = ''

        # Define correct table
        if table == 'Income':
            # Get the data
            income = db.execute("SELECT * FROM income WHERE user_id=:user",
                                {"user": user})
            # Redirect passing in the data
            return render_template("set.html", table_values=income, title="Income", message=message)
        elif table == 'Monthly Budget':
            budget = db.execute("SELECT * FROM monthly WHERE user_id=:user",
                                {"user": user})
            return render_template("set.html", table_values=budget, title="Monthly Budget", message=message)
        elif table == 'Daily Budget':
            budget = db.execute("SELECT * FROM daily WHERE user_id=:user",
                                {"user": user})
            return render_template("set.html", table_values=budget, title="Daily Budget", message=message)
        elif table == 'Savings':
            savings = db.execute("SELECT * FROM savings WHERE user_id=:user",
                                 {"user": user})
            return render_template("set.html", table_values=savings, title="Savings", message=message) 
    
    else:
        return render_template("set.html", message='')


@app.route("/add_row", methods=["POST"])
@login_required
def add_row():
    # Determine user and chose table
    user = login_session['user_id']                
    row_id = request.form.get("row_id")
    t = request.form.get("add_row")
    message = ''
        
    # Get the new values
    item = request.form.get("item")
    value = request.form.get("value")
    fixed = request.form.get("fixed")
    expected = request.form.get("expected")
    
    # For each table
    if t == 'Income':
        # Determine if there is already an item with that name
        name_not_available = db.execute("SELECT FROM income WHERE user_id=:user AND item=:item ",
                                        {"user": user, "item": item}).fetchone()
        # If there isn't an item with that name, update table
        if name_not_available == None:
            db.execute("INSERT INTO income (user_id, item, value) VALUES (:user, :item, :value)",
                       {"user": user, "item": item, "value": value})
        # If there is, return an error message
        else:
            message = 'Item already on the table'
    elif t == 'Monthly Budget':
        name_not_available = db.execute("SELECT FROM monthly WHERE user_id=:user AND item=:item ",
                                        {"user": user, "item": item}).fetchone()
        if name_not_available == None:
            db.execute("INSERT INTO monthly (user_id, item, fixed, expected, spent, available) VALUES (:user, :item, :fixed, :expected, '0', '0')",
                       {"user": user, "item": item, "fixed": fixed, "expected": expected})
        else:
            message = 'Item already on the table'
    elif t == 'Daily Budget':
        name_not_available = db.execute("SELECT FROM daily WHERE user_id=:user AND item=:item ",
                                        {"user": user, "item": item}).fetchone()
        if name_not_available == None:
            db.execute("INSERT INTO daily (user_id, item, fixed, expected, spent, available) VALUES (:user, :item, :fixed, :expected, '0', '0')",
                       {"user": user, "item": item, "fixed": fixed, "expected": expected})
        else:
            message = 'Item already on the table'
    elif t == 'Savings':
        name_not_available = db.execute("SELECT FROM savings WHERE user_id=:user AND item=:item ",
                                        {"user": user, "item": item}).fetchone()
        if name_not_available == None:
            db.execute("INSERT INTO savings (user_id, item, fixed, expected, saved, available) VALUES (:user, :item, :fixed, :expected, '0', '0')",
                       {"user": user, "item": item, "fixed": fixed, "expected": expected})
        else:
            message = 'Item already on the table'
    # Commit changes
    db.commit()

    # Redirect
    if t == 'Income':
        income = db.execute("SELECT * FROM income WHERE user_id=:user",
                            {"user": user})
        return render_template("set.html", table_values=income, title="Income", message=message)
    elif t == 'Monthly Budget':
        budget = db.execute("SELECT * FROM monthly WHERE user_id=:user",
                            {"user": user})
        return render_template("set.html", table_values=budget, title="Monthly Budget", message=message)

    elif t == 'Daily Budget':
        budget = db.execute("SELECT * FROM daily WHERE user_id=:user",
                            {"user": user})
        return render_template("set.html", table_values=budget, title="Daily Budget", message=message)

    elif t == 'Savings':
        savings = db.execute("SELECT * FROM savings WHERE user_id=:user",
                             {"user": user})
        return render_template("set.html", table_values=savings, title="Savings", message=message) 


@app.route("/update_table", methods=["POST"])
@login_required
def update_table():
    # Determine user and chosen table/row
    user = login_session['user_id']            
    row_id = request.form.get("row_id")
    table_id = request.form.get("table_id")

    # Remove Button
    btn = request.form.get("remove_btn")
    if btn != None:
        # Remove row according to the table
        if table_id == 'Income':
            db.execute("DELETE FROM income WHERE user_id=:user AND id=:id",
                       {"user": user, "id": row_id})
        elif table_id == 'Monthly Budget':
            db.execute("DELETE FROM monthly WHERE user_id=:user AND id=:id",
                       {"user": user, "id": row_id})
        elif table_id == 'Daily Budget':
            db.execute("DELETE FROM daily WHERE user_id=:user AND id=:id",
                       {"user": user, "id": row_id})
        elif table_id == 'Savings':
            db.execute("DELETE FROM savings WHERE user_id=:user AND id=:id",
                       {"user": user, "id": row_id})
        db.commit()

    # "Save" button
    else:
        btn = request.form.get("save_btn")
        if btn != None:
            # Determine new values
            item = request.form.get("set_item")
            value = request.form.get("set_value")
            fixed = request.form.get("set_fixed")
            expected = request.form.get("set_expected")

            # Update appropriate table
            if table_id == 'Income':
                db.execute("UPDATE income SET item=:item, value=:value WHERE user_id=:user AND id=:row_id",
                           {"value": value, "item": item, "user": user, "row_id": row_id})
            elif table_id == 'Monthly Budget':
                db.execute("UPDATE monthly SET item=:item, fixed=:fixed, expected=:expected WHERE user_id=:user AND id=:row_id",
                           {"item": item, "fixed": fixed, "expected": expected, "user": user, "row_id": row_id})                        
            elif table_id == 'Daily Budget':
                db.execute("UPDATE daily SET item=:item, fixed=:fixed, expected=:expected WHERE user_id=:user AND id=:row_id",
                           {"item": item, "fixed": fixed, "expected": expected, "user": user, "row_id": row_id})  
            elif table_id == 'Savings':
                db.execute("UPDATE savings SET item=:item, fixed=:fixed, expected=:expected WHERE user_id=:user AND id=:row_id",
                           {"item": item, "fixed": fixed, "expected": expected, "user": user, "row_id": row_id})  
            db.commit()

    # Redirect
    if table_id == 'Income':
        income = db.execute("SELECT * FROM income WHERE user_id=:user",
                            {"user": user})
        return render_template("set.html", table_values=income, title="Income", message="Success")
    elif table_id == 'Monthly Budget':
        budget = db.execute("SELECT * FROM monthly WHERE user_id=:user",
                            {"user": user})
        return render_template("set.html", table_values=budget, title="Monthly Budget", message="Success.")

    elif table_id == 'Daily Budget':
        budget = db.execute("SELECT * FROM daily WHERE user_id=:user",
                            {"user": user})
        return render_template("set.html", table_values=budget, title="Daily Budget", message="Success.")

    elif table_id == 'Savings':
        savings = db.execute("SELECT * FROM savings WHERE user_id=:user",
                             {"user": user})
        return render_template("set.html", table_values=savings, title="Savings", message="Success") 


@app.route("/add_spend", methods=["GET", "POST"])
@login_required
def add_spend():
    if request.method == "POST":
        # Determine user and chosen table/row
        table = request.form.get("chosen_table")
        user = login_session['user_id']
        value = request.form.get("price")
        
        # In case an price was not inputed, just return the row options
        if not value:
            if table == 'Monthly Budget':
                budget = db.execute("SELECT * FROM monthly WHERE user_id=:user",
                                    {"user": user})
                return render_template("add_spend.html", table_rows=budget, table=table)

            elif table == 'Daily Budget':
                budget = db.execute("SELECT * FROM daily WHERE user_id=:user",
                                    {"user": user})
                return render_template("add_spend.html", table_rows=budget, table=table) 
            return render_template("add_spend.html")
        
        # In case the price was inputed:
        else:
            # Get the values
            row = request.form.get("chosen_row")    
            store = request.form.get("store")
            payment = request.form.get("payment")
            obs = request.form.get("obs")
            
            # In case there is not table, return error
            if not row or not table:
                return render_template("add_spend.html", warning='failure')
            
            # Update the purchase table
            db.execute("INSERT INTO purchase (user_id, origin_table, row_id, value, store, payment, obs) VALUES (:user, :table, :row, :value, :store, :payment, :obs)",
                       {"user": user, "table": table, "row": row, "value": value, "store": store, "payment": payment, "obs": obs})
            db.commit()

            # Update the appropriate table 
            if table == 'Monthly Budget':
                update_table = db.execute("SELECT * FROM monthly WHERE user_id=:user AND item=:row",
                                          {"user": user, "row": row}).fetchone()
                spent = float(update_table['spent']) + float(value)
                available = update_table['expected'] - spent
                print(f"update_table {update_table} spent {spent} available {available}")
                db.execute("UPDATE monthly SET spent=:spent, available=:available WHERE user_id=:user AND item=:row",
                           {"spent": spent, "available": available, "user": user, "row": row})
                db.commit()
            elif table == 'Daily Budget':
                update_table = db.execute("SELECT * FROM daily WHERE user_id=:user AND item=:row",
                                          {"user": user, "row": row}).fetchone()
                spent = float(update_table['spent']) + float(value)
                available = update_table['expected'] - spent
                print(f"update_table {update_table} spent {spent} available {available}")
                db.execute("UPDATE daily SET spent=:spent, available=:available WHERE user_id=:user AND item=:row",
                           {"spent": spent, "available": available, "user": user, "row": row})
                db.commit()

            return render_template("add_spend.html", warning='success')

    else:

        return render_template("add_spend.html")


@app.route("/add_savings", methods=["GET", "POST"])
@login_required
def add_savings():
    # Define user
    user = login_session['user_id']

    if request.method == "POST":
        # Define values
        row = request.form.get("chosen_row")
        value = request.form.get("value")
        obs = request.form.get("obs")

        # Insert into savings_transactions table
        db.execute("INSERT INTO savings_transactions (user_id, row_id, value, obs) VALUES (:user, :row, :value, :obs)",
                   {"user": user, "row": row, "value": value, "obs": obs})
        
        # Update values on the savings table
        update_table = db.execute("SELECT * FROM savings WHERE user_id=:user AND item=:row",
                                  {"user": user, "row": row}).fetchone()
        saved = float(update_table['saved']) + float(value)
        available = saved
        db.execute("UPDATE savings SET saved=:saved, available=:available WHERE user_id=:user AND item=:row",
                   {"saved": saved, "available": available, "user": user, "row": row})
        db.commit()

        return render_template("add_savings.html", warning="success")

    else:
        rows = db.execute("SELECT * FROM savings WHERE user_id=:user",
                          {"user": user})
        return render_template("add_savings.html", table_rows=rows)


@app.route("/history")
@login_required
def history():
    # Define user
    user = login_session['user_id']

    # Define table
    table_info = request.args.get('table').split("'")
    table = table_info[1]
    
    # Define item
    row_info = request.args.get('i').split(",")
    item_quotes = row_info[2].split("'")
    item = item_quotes[1]

    # Return page according to the table and pass in the data
    if table == 'Savings':
        info = db.execute("SELECT * FROM savings_transactions WHERE user_id=:user AND row_id=:row",
                          {"user": user, "row": item})
        db.commit()
        return render_template("history_savings.html", info=info, table=table, item=item)
    else:
        info = db.execute("SELECT * FROM purchase WHERE user_id=:user AND origin_table=:table AND row_id=:row",
                          {"user": user, "table": table, "row": item})
        db.commit()
        return render_template("history.html", info=info, table=table, item=item)
    