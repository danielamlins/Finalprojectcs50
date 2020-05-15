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
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@login_required
def index():
    t = request.form.get("chosen_table")
    user = login_session['user_id']
    
    income = db.execute("SELECT * FROM income WHERE user_id=:user",
                    {"user":user})
    budget_monthly = db.execute("SELECT * FROM monthly WHERE user_id=:user",
                    {"user":user})

    budget_daily = db.execute("SELECT * FROM monthly WHERE user_id=:user",
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

        return redirect("/")

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
        
        print(f"first t = {t}")
        # Determine if this route was called by the table selection or by the "add row" menu.
        if t == None:
            t = request.form.get("add_row")
            print(f"third t = {t}")
            #Update table
            item = request.form.get("item")
            value = request.form.get("value")
            fixed = request.form.get("fixed")
            expected = request.form.get("expected")
            if t == 'Income':
                print(f"item {item} value {value}")
                x =  db.execute("SELECT * FROM income WHERE user_id=:user AND item = :item",
                                {"user_id":user, "item":item}).fetchone()
                if x != None:
                    return render_template("set.html", warning="Iten already registered")
                else:
                    db.execute("INSERT INTO income (user_id, item, value) VALUES (:user, :item, :value)",
                            {"user":user, "item":item, "value":value})

            elif t == 'Monthly Budget':
                db.execute("INSERT INTO monthly (user_id, item, fixed, expected, spent, available) VALUES (:user, :item, :fixed, :expected, '0', '0')",
                            {"user":user, "item":item, "fixed":fixed, "expected":expected})

            elif t == 'Daily Budget':
                db.execute("INSERT INTO daily (user_id, item, fixed, expected, spent, available) VALUES (:user, :item, :fixed, :expected, '0', '0')",
                            {"user":user, "item":item, "fixed":fixed, "expected":expected})

            elif t == 'Savings':
                db.execute("INSERT INTO savings (user_id, item, fixed, expected, saved, available) VALUES (:user, :item, :fixed, :expected, '0', '0')",
                            {"user":user, "item":item, "fixed":fixed, "expected":expected})
            db.commit()
        
        #Redirect to correct page
        if t == 'Income':
            income = db.execute("SELECT * FROM income WHERE user_id=:user",
                    {"user":user})
            return render_template("set.html", table_values = income, title="Income" )
        elif t == 'Monthly Budget':
            budget = db.execute("SELECT * FROM monthly WHERE user_id=:user",
                    {"user":user})
            return render_template("set.html", table_values = budget, title="Monthly Budget")

        elif t == 'Daily Budget' :
            budget = db.execute("SELECT * FROM daily WHERE user_id=:user",
                    {"user":user})
            return render_template("set.html", table_values = budget, title="Daily Budget")

        elif t == 'Savings':
            savings = db.execute("SELECT * FROM savings WHERE user_id=:user",
                    {"user":user})
            return render_template("set.html", table_values = savings, title="Savings") 

        
  
        return render_template("set.html", title="Not ok")

    else:
        return render_template("set.html")


@app.route("/add_spend", methods=["GET", "POST"])
@login_required
def add_spend():
    if request.method=="POST":
        # Determine user and chosen table
        t = request.form.get("chosen_table")
        user = login_session['user_id']
        item = request.form.get("item_bought")
        print(f"table new item={t}")

        # Only the table was chosen
        if not item:
            if t == 'Income':
                income = db.execute("SELECT * FROM income WHERE user_id=:user",
                        {"user":user})
                return render_template("add_spend.html", table_rows = income, table = t)
            elif t == 'Monthly Budget':
                budget = db.execute("SELECT item FROM monthly WHERE user_id=:user",
                        {"user":user})
                return render_template("add_spend.html", table_rows = budget, table = t)

            elif t == 'Daily Budget' :
                budget = db.execute("SELECT item FROM monthly WHERE user_id=:user",
                        {"user":user})
                return render_template("add_spend.html", table_rows = budget, table = t)

            elif t == 'Savings':
                savings = db.execute("SELECT item FROM savings WHERE user_id=:user",
                        {"user":user})
                return render_template("add_spend.html", table_rows = savings, table = t) 
            return render_template("add_spend.html")
        
        else:
            row =  request.form.get("chosen_row")
            if not row or not t:
                return render_template("add_spend.html", warning='failure')

            
            value = request.form.get("item_bought")
            item = request.form.get("price")
            store = request.form.get("store")
            payment = request.form.get("payment")
            obs = request.form.get("obs")
            print(f"table {t} row {row} value {value} item {item} store {store} pay {payment} obs {obs}")
            #db.execute(INSERT INTO purchase (user_id, origin_table, ))
            return render_template("add_spend.html", warning='success')

    else:
        return render_template("add_spend.html")


