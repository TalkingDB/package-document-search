import os

from talkingdb.clients.sqlite import sqlite_conn

SEARCH_DB = os.getenv("SEARCH_DB", "data/search.db")


def init_db(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS namespace_configs (
            namespace TEXT PRIMARY KEY,
            vector_search_enabled INTEGER NOT NULL DEFAULT 1,
            keyword_search_enabled INTEGER NOT NULL DEFAULT 1,
            output_fields TEXT NOT NULL DEFAULT '[]'
        )
        """
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS keyword_index USING fts5(
            namespace UNINDEXED,
            partition UNINDEXED,
            doc_id UNINDEXED,
            field_name UNINDEXED,
            value
        )
        """
    )


search_conn = sqlite_conn(SEARCH_DB).__enter__()
init_db(search_conn)
