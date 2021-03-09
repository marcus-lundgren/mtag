import sqlite3
from typing import Dict, List

from mtag.entity import Category


class CategoryRepository:
    def insert(self, conn: sqlite3.Connection, category: Category) -> int:
        cursor = conn.execute("INSERT INTO category (c_name) VALUES (:name)", {"name": category.name})
        conn.commit()
        return cursor.lastrowid

    def get_all(self, conn: sqlite3.Connection) -> List[Category]:
        cursor = conn.execute("SELECT * FROM category ORDER BY lower(c_name) ASC")
        db_categories = cursor.fetchall()

        categories = []
        for db_c in db_categories:
            c = self._from_dbo(db_c)
            categories.append(c)

        return categories

    def get(self, conn: sqlite3.Connection, db_id: int) -> Category:
        cursor = conn.execute("SELECT * FROM category WHERE c_id=:db_id", {"db_id": db_id})
        db_c = cursor.fetchone()
        return self._from_dbo(db_c)

    def update(self, conn: sqlite3.Connection, category: Category) -> None:
        cursor = conn.execute("UPDATE category SET c_url=:url, c_name=:name WHERE c_id=:db_id",
                              {"url": category.url, "name": category.name, "db_id": category.db_id})
        conn.commit()
        cursor.close()

    def _from_dbo(self, db_c: Dict) -> Category:
        return Category(name=db_c["c_name"], db_id=db_c["c_id"], url=db_c["c_url"])
