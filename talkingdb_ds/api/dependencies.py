import sqlite3

from talkingdb_ds.services.db import search_conn


def get_search_conn() -> sqlite3.Connection:
    return search_conn
