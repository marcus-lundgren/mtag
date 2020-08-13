import sqlite3
from entity.category import Category


class CategoryRepository:
    @staticmethod
    def insert(conn: sqlite3.Connection, category: Category):
        conn.execute("INSERT INTO category (c_name) VALUES (:name)", {"name": category.name})
        conn.commit()

    @staticmethod
    def get_all(conn: sqlite3.Connection):
        cursor = conn.execute("SELECT * FROM category")
        db_categories = cursor.fetchall()

        categories = []
        for db_c in db_categories:
            c = Category(name=db_c["c_name"], db_id=db_c["c_id"])
            categories.append(c)

        return categories
