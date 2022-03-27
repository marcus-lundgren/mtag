from mtag.helper import database_helper
from mtag.repository.tagged_entry_repository import TaggedEntryRepository


tagged_entry_repository = TaggedEntryRepository()


def get_total_category_tagged_time(main_name: str, sub_name: str) -> int:
    with database_helper.create_connection() as conn:
        total_time = tagged_entry_repository.total_time_by_category_by_name(conn=conn, main_name=main_name, sub_name=sub_name)
    return total_time

def get_total_category_tagged_time_by_id(category_id: str) -> int:
    with database_helper.create_connection() as conn:
        total_time = tagged_entry_repository.total_time_by_category_by_id(conn=conn, category_id=category_id)
    return total_time
