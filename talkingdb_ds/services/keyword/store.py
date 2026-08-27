import re
import sqlite3

from talkingdb_ds.services.keyword.stopwords import remove_stop_words

_TOKEN_PATTERN = re.compile(r"[\w\-\d./]+")
_FTS_SPECIAL = re.compile(r'["*^:]')


def tokenize(query: str) -> list[str]:
    tokens = _TOKEN_PATTERN.findall(query)
    return [re.sub(r"^\W+|\W+$", "", t) for t in tokens if t]


def index_document(
    conn: sqlite3.Connection,
    namespace: str,
    doc_id: str,
    fields: dict,
    partition: str | None = None,
) -> None:
    delete_document(conn, namespace, doc_id)

    for field_name, value in fields.items():
        if isinstance(value, str) and value:
            conn.execute(
                """
                INSERT INTO keyword_index
                    (namespace, partition, doc_id, field_name, value)
                VALUES (?, ?, ?, ?, ?)
                """,
                (namespace, partition, doc_id, field_name, value),
            )


def delete_document(conn: sqlite3.Connection, namespace: str, doc_id: str) -> None:
    conn.execute(
        "DELETE FROM keyword_index WHERE namespace = ? AND doc_id = ?",
        (namespace, doc_id),
    )


def _fts_query(tokens: list[str]) -> str:
    escaped = [f'"{_FTS_SPECIAL.sub(" ", t)}"' for t in tokens if t]
    return " OR ".join(escaped)


def search(
    conn: sqlite3.Connection,
    query: str,
    namespace: str,
    field_name: str,
    limit: int,
) -> tuple[list[str], list[dict]]:
    tokens = remove_stop_words(tokenize(query))

    if not tokens:
        return [], []

    fts_query = _fts_query(tokens)

    rows = conn.execute(
        """
        SELECT doc_id, value, bm25(keyword_index) AS rank
        FROM keyword_index
        WHERE namespace = ? AND field_name = ? AND keyword_index MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (namespace, field_name, fts_query, limit),
    ).fetchall()

    results = [
        {"id": row["doc_id"], field_name: row["value"], "rank": row["rank"]}
        for row in rows
    ]

    return tokens, results
