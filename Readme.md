# Welcome!

The "Try to Budget" Project is an application that allows the user to organize financial information. On the website, the user will be able to set the budget tables, to write down all expenses (included money saved for specific purposes), and to access all this data in an organized manner.

In this file, I will explain how the website works and the corresponding source.

# Running locally:

You can run this project as a development environment, pointing the environment variables to a public Heroku database: 

```bash
export FLASK_APP=application.py

export FLASK_DEBUG=1

export DATABASE_URL=postgres://qfdnwzywanmsfc:f35a3f7265cf1d77c3830b80b5fa8a2ee52fd0c5dbe57e12c6899f957f6aae65@ec2-54-75-246-118.eu-west-1.compute.amazonaws.com:5432/d4bj04sp4c9slq
```

After that, you should install the requirements provided by `requirements.txt`:

```bash
pip3 install -r requirements.txt
```
To actually run the application locally:

```bash
flask run --host=0.0.0.0
```

# Source Structure:

The source code is organized in an application file written in Python, a database called finalproject.db, a requirements text, a static folder, and a templates folder, containing the html pages.

## Application.py:

As you can see on the exported environment variables, we defined application.py as the starting point of this application.

On the beginning on the file we import the relevant libraries and state that we are going to serve a flask application. On the line [15](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#L15) we check whether the environment variable were set, and, if not, return an error. Then, on line [20](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#20) we configure the session and on line [25](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#25) we set the database.

On line [29](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#29) we define the login_required function, which will only allow access to determined routes when the user is logged in.

### /landing route
From line [43](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#43) onward, the file is divided in different routes that will redirect the user to the corresponding html page. The first route is called `/` and will render the `landing.html` file. On this landing page, the user will have access to the general concepts of this project, and be invited to log in or to register. 

### /register route
Both the `/login` and `/register` routes follow simple standards. On the `/register` route (line [48](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#48)), `register.html` will be rendered and provide the user with a form composed of desired username, password, and a field for password confirmation. The username must include four or more characters and the password must include 8 or more characters. If those requirements are not met, the form will not be submitted. If the password confirmation does not match the password, the page will return a simple message to invite the user to type matching passwords. Then, the `/register` route will query the table 'users' on the database to check if the username is already being used. If it is, the page will return a simple error 'not available'. Otherwise, the user will be registered on the 'users' table. The `/register` route will then initialize the 4 tables of the application, 'income', 'monthly', 'daily' and 'savings' each with one default row. The user will be redirected to the login page with a success message.

### /login route
On the `/login` route (line [88](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#88)), the `login.html` will be rendered. On this page, a simple form with a username and a password field are provided. When submitted, the database will be queried to the username. If it is not registered, a 'Invalid username' alert will show. If it is, the database will be queried for the password. The user will be logged in, in case the password is correct or a 'wrong password and/or username' message will be shown.

### /app route
Once logged in, the user will have access to new routes and will be automatically redirected to the `/app` route (line [118](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#118)). On this route, the 'income', 'monthly', 'daily' and 'savings' tables are queried for all information from this user and these values are saved in variables, which will be then passed in the `index.html` template. On the index page, 4 tables, equivalent to the tables on the database, will be shown, as well as a new row with the total amount for each column of each table. The heading of these tables are clickable and have the action of toggling the respective table. Also, the 'Spent' cells on the 'Monthly Budget', 'Daily Budget' table, as well as the 'Saved' cells on the 'Savings' table are clickable, and will redirect the user to the `/history` route (line [427](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#427))

### /set route and /update_table route
The `/set` route (line [145](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#145)) will render a `set.html` page. When the user first accesses this page, it will only show a Select menu, each option a different table. When a table is chosen, this route will query the database for the rows of this user's table. This data will be passed in so that a table with this information can be rendered. This table is composed of a form for each cell. These forms have placeholders equivalent to the actual value of that row. When we want to update this value, we can simply write down on the form the new value and click 'save'. The value must be a number with a maximum of 2 decimal places (negative allowed) for every column, except for the 'item' column, which allows a text input. The 'spent', 'available' and 'saved' columns may not be edited, once these values are automatically set by the `/add_spend` and `/add_savings` routes (lines [328](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#328) and [394](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#394), respectively). If we desire to delete a row, we can choose the 'delete' button. Both buttons will call the `/update_table` route (line [256](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#256)). This route will initially determine which table and row are chosen, as well as the user in session. If the 'remove' button was clicked, it will delete that row on the respective table on the database. If the 'save' button was clicked, new variables for each of the new values are declared, and the row on the respective table on the database will be updated. The `set.html` page will be, again rendered, and show the table with the new values.

### /add_row route
Also on the `set.html` page, at the same time as the table is rendered, a form that allows us to add a new row to that table is shown. All the fields are required for us to be able submit this form. The input of the 'item' field is a text, while the other fields require a number with a maximum of 2 decimal places. Negative number are allowed. When submitted, the `/add_row` (line [180](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#180)) route will be run. First, it will determine the user, the row and the table in question. A 'message' variable is also initialized. Then, the route will get the inputted values. The database is queried (according to the table selected) and it is determined whether a row with that name is available. If not, a message 'Item already in the database' is shown to the user. Otherwise, this new row is inserted into the table. Then, the set.html is again rendered showing the selected table, already showing the newly added row.

### /add_spend route
The `/add_spend` route renders the `add_spend.html` page, which shows us a form composed of a selection menu and 4 input fields ('price', 'store', 'payment' and 'observations'). The 'price' field requires a number with a maximum of 2 decimals. A text can be inputted to the following three fields, but these are not required. If left blank, they will return a value of '-'. 

On the selection menu, each table is shown as an option.  When a table is chosen, the form will be submitted, and the route will check if the user inputted a value to the 'price' field. If not, it will query the database, to determine the rows of the chosen table. The `add_spend.html` is again rendered showing a second selection menu (between the selection menu and the following fields), whose options are the rows of the table. If the user first inputs the 'price' field and then the table selection menu, the page will automatically submit. To avoid a null value for the row, in these cases, an error ('failure') will be rendered (line [357](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#357)). 

In case all the required fields ('table', 'row' and 'price') are met, the route will update the 'purchase' table, which store every transaction on the 'monthly' and 'daily' tables. The route will then determine the new value for the 'spend' row and 'available' row on the corresponding table. `add_savings.html` will again be rendered with a 'success' message.

### /add savings route
The `/add_spend` and `/add_savings` routes are similar. The latter (line [393](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#393) renders the `add_savings.html` page. This page is composed of a form with a selection menu and 3 input fields. The selection menu allows us to choose a 'savings' category (equivalent to a row of the table). The value field requires a number with a maximum of 2 decimal fields (negative allowed), and must be filled before submitting. The 'observation' field is not mandatory and, if left blank, will return '-' as value. When the form is submitted, the 'savings_transactions' tables is updated. Similarly, the columns 'saved' and 'available' of the 'savings' table are updated. Then, the `add_savings.html` is again rendered with a 'success' message.

### /history route
As stated before, the `/history` route is accessed when we click on the cells of the 'spent' or 'saved' columns on the index page. The `/history` route receives data through the URL parameter. This data allows the route to identify the origin of the clicked cell(which table and which row). These arguments are treated and the database is then queried for the information on the 'purchase' table (when the data comes from the 'Monthly Budget' or the 'Daily Budget' tables) or the 'transactions_savings' table (when the data comes from the 'Savings' table). This information is passed in the `history.html` or `history_savings.html` pages, respectively. These pages will show, therefore, a table with a history of the expenses/savings on the chosen category.

### Database

This application uses a Heroku public database. The tables are already created as following:

### Users

This table is used to determine the sessions. Every user has a unique serial id, a username and a hashcode referent to the password.

### Income, monthly, daily and savings

These are the 4 basic tables that allows us to organize our finances. 

The income table allows the user to write down all the income sources. The columns are the user_id, which relates the user.id column, a unique id, the item (name of the income source) and the value.

The monthly table is used to store information of expenses that are paid on a monthly basis (such as rent, installments, water bills, etc). The daily table is used to store information of expenses that are (or can be) paid more than once a month, such as food, transportation, leisure activities, etc. The structure is similar to the 'monthly' table, and both are composed of a user_id (related to the user.id column), and a unique serial id, the name of the item (or category), the fixed value (how much the user should expend every month), the expected value (how much it is expected to spend this month), how much was spent (which will be automatically updated when the user uses the `/add_spend` route to include new purchases) and how much is available (automatically calculated as a difference between the 'expected' value and the 'spent' value).

The savings table, in turn, is used to store data about the money saved with specific purpose/goal. It is composed of a user_id (related to the user.id column), and unique serial id, the name of the item (or category), the fixed value (how much the user should save every month), the expected value (how much it is expected to save this month), how much was saved (which will be automatically updated when the user uses the `/add_savings` route to include new saved values) and how much is available (saved in total).

### Purchase and savings_transactions

Both these tables were created to store the data of each input to the `/add_spend` and `/add_expenses` route. The purchase table is composed of a user_id (related to users.id), a unique serial id, the origin_table (related to ehich table this expense was added), row_id (related to which row/category this expense was added to), value (price paid), store (where the user can store where the item was bought), payment (to store information of the payment method, whether card, and which card, cash, etc), observations, and a date (default to current timestamp).

The 'savings_transactions' is similar, but is included fewer rows: a user_id (related to users.id), a unique serial id, the origin_table (related to which table this expense was added), row_id (related to which row/category this expense was added to), value (price paid), observations and date (default to current timestamp)

## Style

The style of the page is defined by the `layout.html` page. Further code regarding the styling on the page can be found on the static folder. 

Several style definitions were imported from this [theme](https://github.com/BlackrockDigital/startbootstrap-agency) with some adaptations to blend with my project. Styles that are exclusive to my application pages can be found on `static/styles.css`. The styles adapted from [boostrap-agency](https://github.com/BlackrockDigital/startbootstrap-agency) can be found on `static/styles-landing.css`