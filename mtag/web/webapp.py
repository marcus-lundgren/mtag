from datetime import datetime, date
import json
import re
import os
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs

from ..entity import Category, LoggedEntry, ApplicationWindow, Application, TaggedEntry, ActivityEntry
from ..helper import database_helper
from ..helper.statistics_helper import get_total_category_tagged_time_by_id, get_total_category_tagged_time
from ..repository import CategoryRepository, LoggedEntryRepository, TaggedEntryRepository, ActivityEntryRepository

date_validator = re.compile(r"\d\d\d\d-\d\d-\d\d")
file_paths = {
    "/": "www/index.html",
    "/index.html": "www/index.html",
    "/categories.html": "www/categories.html",
    "/settings.html": "www/settings.html",
    "/about.html": "www/about.html",
    "/static/js/api_client.js": "www/static/js/api_client.js",
    "/static/js/category_page.js": "www/static/js/category_page.js",
    "/static/js/timeline.js": "www/static/js/timeline.js",
    "/static/js/timeline_minimap.js": "www/static/js/timeline_minimap.js",
    "/static/js/timeline_modal.js": "www/static/js/timeline_modal.js",
    "/static/js/timeline_page.js": "www/static/js/timeline_page.js",
    "/static/js/timeline_utilities.js": "www/static/js/timeline_utilities.js",
    "/static/css/styles.css": "www/static/css/styles.css",
}


class RequestHandler(BaseHTTPRequestHandler):
    def _set_json_response(self, obj) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

    def _set_string_response(self, string_response: str, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(string_response.encode("utf-8"))

    def _set_ok_without_content(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

    def _set_not_found_response(self) -> None:
        self.send_response(404)

    def _set_bad_request_response(self) -> None:
        self.send_response(400)

    def do_GET(self):
        # Static files
        if self.path in file_paths:
            p: str = self._get_local_file_path(file_paths[self.path])
            file_contents = self._get_file_contents(p)

            if p.endswith(".html"):
                content_type: str = "text/html"
                file_contents = self._html_page_loader(file_contents)
            elif p.endswith(".js"):
                content_type = "text/javascript"
            elif p.endswith(".css"):
                content_type = "text/css"
            self._set_string_response(file_contents, content_type)
        elif self.path.startswith("/entries/"):
            date_string = self.path[len("/entries/"):]

            # Ensure that we got the date in the expected format
            if date_validator.match(date_string) == None:
                self._set_bad_request_response
                return

            date_date = date.fromisoformat(date_string)
            with database_helper.create_connection() as conn:
                logged_entries = LoggedEntryRepository().get_all_by_date(conn=conn, date=date_date)
                tagged_entries = TaggedEntryRepository().get_all_by_date(conn=conn, date=date_date)
                activity_entries = ActivityEntryRepository().get_all_by_date(conn=conn, date=date_date)
            self._set_json_response({
                "logged_entries": [logged_entry_to_json(le) for le in logged_entries],
                "tagged_entries": [tagged_entry_to_json(te) for te in tagged_entries],
                "activity_entries": [activity_entry_to_json(ae) for ae in activity_entries]
            })
        elif self.path.startswith("/categories"):
            with database_helper.create_connection() as conn:
                categories = CategoryRepository().get_all(conn=conn)
            self._set_json_response([{"main": category_to_json(main), "children": [category_to_json(c) for c in children]} for (main, children) in categories])
        elif self.path.startswith(("/category/statistics")):
            params = parse_qs(self.path.split("?")[1])

            if "main" in params:
                main = params["main"][0]
                sub = params["sub"][0] if "sub" in params else None
                seconds = get_total_category_tagged_time(main_name=main, sub_name=sub)
            else:
                raise Exception("Statistics requires main and optional sub")

            self._set_json_response({"seconds": seconds})
        elif self.path.startswith("/category/"):
            db_id = self.path[len("/category/"):]
            throw_if_not_digit(db_id)

            category_repository = CategoryRepository()
            with database_helper.create_connection() as conn:
                category = category_repository.get(conn=conn, db_id=db_id)
                subs = category_repository.get_all_subs(conn=conn, db_id=db_id)
            json = category_to_json(category)
            json["seconds"] = get_total_category_tagged_time_by_id(category.db_id)
            json["has_subs"] = len(subs) > 0
            self._set_json_response(json)
        else:
            self._set_not_found_response()

    def do_POST(self):
        print("POST called")
        print("----", self.path)

        if self.path == "/taggedentry/add":
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            main_name = data["main"].strip()
            if len(main_name) == 0:
                raise Exception("Main category is null or whitespace")

            sub_name = data["sub"]
            if sub_name is not None:
                if len(sub_name.strip()) == 0:
                    raise Exception("Sub category is empty or whitespace")
                sub_name = sub_name.strip()

            tagged_entry = TaggedEntry(
                start=datetime.fromisoformat(data["start"]),
                stop=datetime.fromisoformat(data["stop"]),
                category=None)
            with database_helper.create_connection() as conn:
                category_repository = CategoryRepository()
                tagged_entry.category = category_repository.insert(
                    conn=conn,
                    main_name=data["main"],
                    sub_name=data["sub"])
                TaggedEntryRepository().insert(conn=conn, tagged_entry=tagged_entry)
                self._set_ok_without_content()
        elif self.path == "/category/edit":
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            db_id = data["id"]
            name = data["name"].strip()
            url = data["url"].strip()
            parent_id = data["parentId"]

            throw_if_not_digit(db_id)
            if len(name) == 0:
                raise Exception("Name is not allowed to be empty")

            if parent_id is not None:
                throw_if_not_digit(parent_id)

                # Ensure that we aren't a main category with sub categories
                with database_helper.create_connection() as conn:
                    subs = CategoryRepository().get_all_subs(conn=conn, db_id=db_id)
                if len(subs) > 0:
                    raise Exception("Cannot change parent of a category with existing sub categories")

            category = Category(db_id=db_id, name=name, url=url, parent_id=parent_id)
            with database_helper.create_connection() as conn:
                CategoryRepository().update(conn=conn, category=category)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

    def do_DELETE(self):
        print("DELETE called")
        print("----", self.path)

        if self.path.startswith("/taggedentry/"):
            db_id = self.path[len("/taggedentry/"):]
            throw_if_not_digit(db_id)

            print("Deleting tagged entry with ID:", db_id)
            with database_helper.create_connection() as conn:
                TaggedEntryRepository().delete(conn=conn, db_id=db_id)
            self._set_ok_without_content()
        elif self.path.startswith("/category/"):
            db_id = self.path[len("/category/"):]
            throw_if_not_digit(db_id)

            print("Deleting category with ID:", db_id)
            category_repository = CategoryRepository()
            with database_helper.create_connection() as conn:
                c = category_repository.get(conn=conn, db_id=db_id)
                category_repository.delete(conn=conn, category=c)
            self._set_ok_without_content()
        else:
            self._set_not_found_response()

    def _html_page_loader(self, page_contents: str) -> str:
        html_base_path = self._get_local_file_path("/www/base.html")
        html_base_contents = self._get_file_contents(html_base_path)
        return html_base_contents.replace("<!-- CONTENT -->", page_contents)

    def _get_local_file_path(self, url_path: str) -> str:
        print("############", Path(__file__).parent, url_path)
        return os.path.join(Path(__file__).parent, *url_path.split("/"))

    def _get_file_contents(self, local_path: str) -> str:
        with open(local_path, "r") as f:
            return f.read()


def throw_if_not_digit(num):
    if not num.isdigit():
        raise Exception(f"Value '{num}' is not a digit")

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


def datetime_to_json(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

