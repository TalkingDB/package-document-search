import os
import sqlite3
import tempfile
import uuid

import pytest

# Point vector_store at a throwaway Milvus Lite file for the whole test
# session, before anything imports it - no external Milvus server needed.
_MILVUS_LITE_PATH = os.path.join(
    tempfile.gettempdir(), f"pt-test-{uuid.uuid4().hex}.db"
)
os.environ["DS_MILVUS_URI"] = _MILVUS_LITE_PATH

from talkingdb_ds.services.db import init_db  # noqa: E402


@pytest.fixture
def search_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def namespace():
    # Milvus collection names must be valid identifiers - no dashes.
    return f"test_{uuid.uuid4().hex[:8]}"
