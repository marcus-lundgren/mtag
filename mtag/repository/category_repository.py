import sqlite3
from typing import Dict, List, Tuple, Optional

from mtag.entity import Category


class CategoryRepository:
    def insert(self, conn: sqlite3.Connection, main_name: str, sub_name: Optional[str]) -> Category:
        # Get the main category from the database if it exists
        main_category = self.get_main_by_name(conn=conn, name=main_name)

        if main_category is not None:
            main_category_id = main_category.db_id
        else:
            main_category_id = self.insert_main(conn=conn, name=main_name)

        if sub_name is None:
            return self.get(conn=conn, db_id=main_category_id)

        sub_category = self.get_sub_by_name(conn=conn, name=sub_name, parent_id=main_category_id)
        if sub_category is not None:
            return sub_category

        sub_category_id = self.insert_sub(conn=conn, name=sub_name, parent_id=main_category_id)
        return self.get(conn=conn, db_id=sub_category_id)

    def insert_main(self, conn: sqlite3.Connection, name: str) -> int:
        cursor = conn.execute("INSERT INTO category (c_name) VALUES (:name)", {"name": name})
        conn.commit()
        return cursor.lastrowid

    def insert_sub(self, conn: sqlite3.Connection, name: str, parent_id: int) -> int:
        cursor = conn.execute("INSERT INTO category (c_name, c_parent_id) VALUES (:name, :parent_id)", {"name": name, "parent_id": parent_id})
        conn.commit()
        return cursor.lastrowid

    def get_all_mains(self, conn: sqlite3.Connection) -> List[Category]:
        cursor = conn.execute("SELECT * FROM category WHERE c_parent_id IS NULL ORDER BY lower(c_name) ASC")
        db_categories = cursor.fetchall()
        return [self._from_dbo(db_c) for db_c in db_categories]

    def get_main_by_name(self, conn: sqlite3.Connection, name: str) -> Optional[Category]:
        cursor = conn.execute("SELECT * FROM category WHERE lower(c_name)=lower(:name) AND c_parent_id IS NULL", {"name": name})
        db_c = cursor.fetchone()
        if db_c is None:
            return None
        return self._from_dbo(db_c)

    def get_sub_by_name(self, conn: sqlite3.Connection, name: str, parent_id: int) -> Optional[Category]:
        cursor = conn.execute("SELECT * FROM category WHERE lower(c_name)=lower(:name) AND c_parent_id=:parent_id", {"name": name, "parent_id": parent_id})
        db_c = cursor.fetchone()
        if db_c is None:
            return None
        return self._from_dbo(db_c)

    def get_all_subs(self, conn: sqlite3.Connection, db_id: int) -> List[Category]:
        cursor = conn.execute("SELECT * FROM category WHERE c_parent_id=:db_id ORDER BY lower(c_name) ASC", {"db_id": db_id})
        db_categories = cursor.fetchall()

        return [self._from_dbo(db_c) for db_c in db_categories]

    def get_all(self, conn: sqlite3.Connection) -> List[Tuple[Category, List[Category]]]:
        return [(main, self.get_all_subs(conn=conn, db_id=main.db_id)) for main in self.get_all_mains(conn=conn)]

    def get(self, conn: sqlite3.Connection, db_id: int) -> Category:
        cursor = conn.execute("SELECT * FROM category WHERE c_id=:db_id", {"db_id": db_id})
        db_c = cursor.fetchone()
        return self._from_dbo(db_c)

    def update(self, conn: sqlite3.Connection, category: Category) -> None:
        cursor = conn.execute("UPDATE category SET c_url=:url, c_name=:name WHERE c_id=:db_id",
                              {"url": category.url, "name": category.name, "db_id": category.db_id})
        conn.commit()
        cursor.close()

    def delete(self, conn: sqlite3.Connection, category: Category) -> None:
        cursor = conn.execute("DELETE FROM category WHERE c_id=:db_id",
                              {"db_id": category.db_id})
        conn.commit()
        cursor.close()

    def _from_dbo(self, db_c: Dict) -> Category:
        return Category(name=db_c["c_name"], db_id=db_c["c_id"], url=db_c["c_url"], parent_id=db_c["c_parent_id"])
