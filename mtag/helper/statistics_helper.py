from mtag.helper import database_helper
from mtag.repository.tagged_entry_repository import TaggedEntryRepository


tagged_entry_repository = TaggedEntryRepository()


def get_total_category_tagged_time(category_name: str) -> int:
    conn = database_helper.create_connection()
    total_time = tagged_entry_repository.total_time_by_category(conn=conn, category_name=category_name)
    conn.close()
    return total_time
