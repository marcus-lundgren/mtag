import datetime
from flask import Flask, render_template, request
from ..entity import Category, LoggedEntry, ApplicationWindow, Application, TaggedEntry, ActivityEntry
from ..helper import database_helper
from ..repository import CategoryRepository, LoggedEntryRepository, TaggedEntryRepository, ActivityEntryRepository

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/entries/<date_string>")
def get_logged_entries(date_string: str):
    date_date = datetime.date.fromisoformat(date_string)
    with database_helper.create_connection() as conn:
        logged_entries = LoggedEntryRepository().get_all_by_date(conn=conn, date=date_date)
        tagged_entries = TaggedEntryRepository().get_all_by_date(conn=conn, date=date_date)
        activity_entries = ActivityEntryRepository().get_all_by_date(conn=conn, date=date_date)
    return {
        "logged_entries": [logged_entry_to_json(le) for le in logged_entries],
        "tagged_entries": [tagged_entry_to_json(te) for te in tagged_entries],
        "activity_entries": [activity_entry_to_json(ae) for ae in activity_entries]
    }


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


def activity_entry_to_json(ae: ActivityEntry):
    return {
        "db_id": ae.db_id,
        "active": ae.active,
        "start": datetime_to_json(ae.start),
        "stop": datetime_to_json(ae.stop)
    }


def tagged_entry_to_json(te: TaggedEntry):
    return {
        "db_id": te.db_id,
        "start": datetime_to_json(te.start),
        "stop": datetime_to_json(te.stop),
        # "initial_position": te.self.start,
        "category": category_to_json(te.category),
        "category_str": te.category_str
    }


def category_to_json(c: Category):
    return {
        "db_id": c.db_id,
        "name": c.name,
        "url": c.url,
        "parent_id": c.parent_id
    }

def logged_entry_to_json(le: LoggedEntry):
    return {
        "db_id": le.db_id,
        "start": datetime_to_json(le.start),
        "stop": datetime_to_json(le.stop),
        "application_window": application_window_to_json(le.application_window)
    }

def application_window_to_json(aw: ApplicationWindow):
    return {
        "title": aw.title,
        "application": application_to_json(aw.application),
        "db_id": aw.db_id
    }

def application_to_json(a: Application) -> dict:
    return {
        "db_id": a.db_id,
        # "application_path": a.application_path,
        "name": a.name
    }

def datetime_to_json(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")
