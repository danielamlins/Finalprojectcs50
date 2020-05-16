import os

from flask import Flask, session, render_template, request, redirect
from flask import session as login_session
from flask_session import Session
from tempfile import mkdtemp
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps


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


@app.route("/app")
@login_required
def index():
    t = request.form.get("chosen_table")
    user = login_session['user_id']
    
    income = db.execute("SELECT * FROM income WHERE user_id=:user",
                    {"user":user})
    budget_monthly = db.execute("SELECT * FROM monthly WHERE user_id=:user",
                    {"user":user})

    budget_daily = db.execute("SELECT * FROM daily WHERE user_id=:user",
                    {"user":user})

    savings = db.execute("SELECT * FROM savings WHERE user_id=:user",
                    {"user":user})
    return render_template("index.html", income = income, budget_daily = budget_daily, budget_monthly=budget_monthly, savings=savings)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Make sure the user provided a valid username, password and matching password confirmation
        if not request.form.get("conf_password"):
            return render_template("register.html", no_confir_password='True')
        elif request.form.get("conf_password") != request.form.get("password"):
            return render_template("register.html", no_confir_password='True')

        # Make sure the username is available
        username=request.form.get("username")
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username":username}).fetchone()
        if rows:
            return render_template("register.html",warning='not available')


        # Register the user
        password=generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hashcode) VALUES (:username, :password)", 
                                        {"username":username, "password":password})

        # Initialize tables
        user_info =  db.execute("SELECT * FROM users WHERE username = :username",
                          {"username":username}).fetchone()
        id= user_info["id"]
        db.execute("INSERT INTO income (user_id, item, value) VALUES (:user, 'Salary', '0')",
                    {"user":id})
        db.execute("INSERT INTO monthly (user_id, item, fixed, expected, spent, available) VALUES (:user, 'Rent', '0', '0','0','0')",
                    {"user":id})    
        db.execute("INSERT INTO daily (user_id, item, fixed, expected, spent, available) VALUES (:user, 'Groceries', '0', '0','0','0')",
                    {"user":id})
        db.execute("INSERT INTO savings (user_id, item, fixed, expected, saved, available) VALUES (:user, 'Emergency', '0', '0','0','0')",
                    {"user":id})              
        db.commit()
        return render_template("login.html", warning = 'success')

    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Checking for an existing username
        username=request.form.get("username")
        row = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username":username}).fetchone()

        print(f"row = {row}")

        # Check if the username exists.
        if row == None:
            return render_template("login.html", warning = 'wrong_password', message="Invalid username.")

        # Check if the password is correct
        if not check_password_hash(row["hashcode"], request.form.get("password")):
            return render_template("login.html", warning = 'wrong_password', message="Wrong username and/or password")

        # Begin session and redirect
        session["user_id"] = row[0]

        login_session['username'] = row[1]
        print(f"login session {login_session}")

        return redirect("/app")

    else:
        return render_template("login.html")

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
        t = request.form.get("chosen_table")
        user = login_session['user_id']
                
        row_id = request.form.get("row_id")
        table_id = request.form.get("table_id")

        # Set return message
        message = ''

        # Determine if this route was called by the table selection or by the "add row" menu. 
        # Here, the remove button.
        if row_id != None:
            print(f"table {table_id} row {row_id} user {user}")
            if table_id == 'Income':
                db.execute("DELETE FROM income WHERE user_id=:user AND id=:id",
                            {"user":user, "id":row_id })

            elif table_id == 'Monthly Budget':
                db.execute("DELETE FROM monthly WHERE user_id=:user AND id=:id",
                            {"user":user, "id":row_id })
            elif table_id == 'Daily Budget':
                db.execute("DELETE FROM daily WHERE user_id=:user AND id=:id",
                            {"user":user, "id":row_id })

            elif table_id == 'Savings':
                db.execute("DELETE FROM savings WHERE user_id=:user AND id=:id",
                            {"user":user, "id":row_id })
            db.commit()

            # Set for redirect
            redirect = table_id
        
        #Here the add button.
        elif t == None or t == 'Select table':
            t = request.form.get("add_row")
        
            #Update table
            item = request.form.get("item")
            value = request.form.get("value")
            fixed = request.form.get("fixed")
            expected = request.form.get("expected")
            
            if t == 'Income':
                name_not_available = db.execute("SELECT FROM income WHERE user_id=:user AND item=:item ",
                                                {"user":user, "item":item}).fetchone()
                if name_not_available == None:
                    db.execute("INSERT INTO income (user_id, item, value) VALUES (:user, :item, :value)",
                            {"user":user, "item":item, "value":value})
                else:
                    message = 'Item already on the table'
            elif t == 'Monthly Budget':
                name_not_available = db.execute("SELECT FROM monthly WHERE user_id=:user AND item=:item ",
                                                {"user":user, "item":item}).fetchone()
                if name_not_available == None:
                    db.execute("INSERT INTO monthly (user_id, item, fixed, expected, spent, available) VALUES (:user, :item, :fixed, :expected, '0', '0')",
                            {"user":user, "item":item, "fixed":fixed, "expected":expected })
                else:
                    message = 'Item already on the table'
            elif t == 'Daily Budget':
                name_not_available = db.execute("SELECT FROM daily WHERE user_id=:user AND item=:item ",
                                                {"user":user, "item":item}).fetchone()
                if name_not_available == None:
                    db.execute("INSERT INTO daily (user_id, item, fixed, expected, spent, available) VALUES (:user, :item, :fixed, :expected, '0', '0')",
                            {"user":user, "item":item, "fixed":fixed, "expected":expected })
                else:
                    message = 'Item already on the table'
            elif t == 'Savings':
                name_not_available = db.execute("SELECT FROM savings WHERE user_id=:user AND item=:item ",
                                                {"user":user, "item":item}).fetchone()
                if name_not_available == None:
                    db.execute("INSERT INTO savings (user_id, item, fixed, expected, saved, available) VALUES (:user, :item, :fixed, :expected, '0', '0')",
                            {"user":user, "item":item, "fixed":fixed, "expected":expected })
                else:
                    message = 'Item already on the table'
            db.commit()
            redirect = t

        #here, the selection menu    
        else:
            redirect =  request.form.get("chosen_table")

        #Redirect to correct page
        if redirect == 'Income':
            income = db.execute("SELECT * FROM income WHERE user_id=:user",
                    {"user":user})
            return render_template("set.html", table_values = income, title="Income", message=message )
        elif redirect == 'Monthly Budget':
            budget = db.execute("SELECT * FROM monthly WHERE user_id=:user",
                    {"user":user})
            return render_template("set.html", table_values = budget, title="Monthly Budget", message=message)

        elif redirect == 'Daily Budget':
            budget = db.execute("SELECT * FROM daily WHERE user_id=:user",
                    {"user":user})
            return render_template("set.html", table_values = budget, title="Daily Budget", message=message)

        elif redirect == 'Savings':
            savings = db.execute("SELECT * FROM savings WHERE user_id=:user",
                    {"user":user})
            return render_template("set.html", table_values = savings, title="Savings", message=message) 

        return render_template("set.html", title="Not ok")

    else:
        return render_template("set.html", message= '')


@app.route("/add_spend", methods=["GET", "POST"])
@login_required
def add_spend():
    if request.method=="POST":
        # Determine user and chosen table
        table = request.form.get("chosen_table")
        user = login_session['user_id']
        item = request.form.get("item_bought")

        # Only the table was chosen (the form was not filled but chooding the table will submit the form)
        if not item:
            if table == 'Monthly Budget':
                budget = db.execute("SELECT * FROM monthly WHERE user_id=:user",
                        {"user":user})
                return render_template("add_spend.html", table_rows = budget, table = table)

            elif table == 'Daily Budget' :
                budget = db.execute("SELECT * FROM daily WHERE user_id=:user",
                        {"user":user})
                return render_template("add_spend.html", table_rows = budget, table = table) 
            return render_template("add_spend.html")
        
        else:
            row =  request.form.get("chosen_row")    
            item = request.form.get("item_bought")
            value = request.form.get("price")
            store = request.form.get("store")
            payment = request.form.get("payment")
            obs = request.form.get("obs")
            print(f"table {table} row {row} value {value} item {item} store {store} pay {payment} obs {obs}")
            
            if not row or not table:
                return render_template("add_spend.html", warning='failure')
            
            # Queries
            db.execute("INSERT INTO purchase (user_id, origin_table, row_id, item, value, store, payment, obs) VALUES (:user, :table, :row, :item, :value, :store, :payment, :obs)",
                        {"user":user, "table":table, "row":row, "item":item, "value":value, "store":store, "payment":payment, "obs":obs})
            db.commit()
            if table == 'Monthly Budget':
                update_table = db.execute("SELECT * FROM monthly WHERE user_id=:user AND item=:row",
                                            {"user":user, "row":row}).fetchone()
                spent = float(update_table['spent']) + float(value)
                available = update_table['expected'] - spent
                print(f"update_table {update_table} spent {spent} available {available}")
                db.execute("UPDATE monthly SET spent=:spent, available=:available WHERE user_id=:user AND item=:row",
                            {"spent":spent, "available":available, "user":user, "row":row})
                db.commit()
            elif table == 'Daily Budget':
                update_table = db.execute("SELECT * FROM daily WHERE user_id=:user AND item=:row",
                                            {"user":user, "row":row}).fetchone()
                spent = float(update_table['spent']) + float(value)
                available = update_table['expected'] - spent
                print(f"update_table {update_table} spent {spent} available {available}")
                db.execute("UPDATE daily SET spent=:spent, available=:available WHERE user_id=:user AND item=:row",
                            {"spent":spent, "available":available, "user":user, "row":row})
                db.commit()
            return render_template("add_spend.html", warning='success')

    else:
        return render_template("add_spend.html")



@app.route("/saved", methods=["GET", "POST"])
@login_required
def saved():
    user = login_session['user_id']
    if request.method=="POST":
        row =  request.form.get("chosen_row")
        value = request.form.get("value")
        obs = request.form.get("obs")
        # Insert into savings_transactions table
        db.execute("INSERT INTO savings_transactions (user_id, row_id, value, obs) VALUES (:user, :row, :value, :obs)",
                        {"user":user, "row":row, "value":value, "obs":obs})
        update_table = db.execute("SELECT * FROM savings WHERE user_id=:user AND item=:row",
                        {"user":user, "row":row}).fetchone()
        saved = float(update_table['saved']) + float(value)
        available = update_table['expected'] + saved
        print(f"update_table {update_table} saved {saved} available {available}")
        db.execute("UPDATE savings SET saved=:saved, available=:available WHERE user_id=:user AND item=:row",
                            {"saved":saved, "available":available, "user":user, "row":row})
        db.commit()

        return render_template("saved.html", warning="success")
    else:
        rows= db.execute("SELECT * FROM savings WHERE user_id=:user",
                            {"user":user})
        return render_template("saved.html", table_rows = rows)

@app.route("/history")
@login_required
def history():
    user = login_session['user_id']
    table_info  = request.args.get('table').split("'")
    table = table_info[1]
    
    row_info  = request.args.get('i').split(",")
    item_quotes = row_info[2].split("'")
    item = item_quotes[1]
    
    info = db.execute("SELECT * FROM purchase WHERE  user_id=:user AND origin_table=:table AND item=:item",
                        {"user":user, "table":table, "item":item}).fetchall()
    db.commit()
    print(f"table {table}, item {item} user {user} info {info}")

    return render_template("history.html", info = info, table = table, item = item)
    