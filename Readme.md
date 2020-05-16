# Welcome!

The "Try to Budget" Project is an application that allows the user to organize finantial information. On the website, the user will be able set budget tables, to write down all expenses (included money saved for specific purposes), and to access all this data in an organized manner.

On this file, I will explain how the website works and the corresponding source.

# Running locally:

You can run this project as a development environment pointing the environment variables to a public Heroku databse: 

```bash
export FLASK_APP=application.py

export FLASK_DEBUG=1

export DATABASE_URL=postgres://qfdnwzywanmsfc:f35a3f7265cf1d77c3830b80b5fa8a2ee52fd0c5dbe57e12c6899f957f6aae65@ec2-54-75-246-118.eu-west-1.compute.amazonaws.com:5432/d4bj04sp4c9slq
```

After that, you can install the requirements provided by `requirements.txt`:

```bash
pip3 install -r requirements.txt
```
To actually run the application locally:

```bash
flask run --host=0.0.0.0
```

# Source Structure:

The source code is organized in an application document written in Python, a database called finalproject.db, a requirements text, a static folder, a templates folder and a flask_session folder.

## Application.py:

As you can see on the exported envirnonment variables, we defined application.py as the starting point of this application.

At line [12](https://github.com/danielamlins/Finalprojectcs50/blob/master/application.py#L12) we habe blas
