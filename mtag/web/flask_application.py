from flask import Flask, render_template, request
from ..entity import Category
from ..helper import database_helper
from ..repository import CategoryRepository

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/categories")
def categories():
    # Fetch all main categories
    with database_helper.create_connection() as conn:
        categories = CategoryRepository().get_all(conn)
    return render_template("categories.html", categories=categories)


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/about")
def about():
    return render_template("about.html")
