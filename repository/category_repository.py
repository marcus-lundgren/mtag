import sqlite3
from entity.category import Category


class CategoryRepository:
    def insert(self, conn: sqlite3.Connection, category: Category):
        conn.execute("INSERT INTO category (c_name) VALUES (:name)", {"name": category.name})
        conn.commit()

    def get_all(self, conn: sqlite3.Connection):
        cursor = conn.execute("SELECT * FROM category")
        db_categories = cursor.fetchall()

        categories = []
        for db_c in db_categories:
            c = self._from_dbo(db_c)
            categories.append(c)

        return categories

    def get(self, conn: sqlite3.Connection, db_id: int):
        cursor = conn.execute("SELECT * FROM category WHERE c_id=:db_id", {"db_id": db_id})
        db_c = cursor.fetchone()
        return self._from_dbo(db_c)

    def _from_dbo(self, db_c: dict) -> Category:
        return Category(name=db_c["c_name"], db_id=db_c["c_id"])
