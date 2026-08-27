import json
import sqlite3
from dataclasses import dataclass


@dataclass
class NamespaceConfig:
    namespace: str
    vector_search_enabled: bool = True
    keyword_search_enabled: bool = True
    output_fields: list[str] | None = None

    def __post_init__(self):
        if self.output_fields is None:
            self.output_fields = []


def get_namespace_config(conn: sqlite3.Connection, namespace: str) -> NamespaceConfig:
    row = conn.execute(
        "SELECT * FROM namespace_configs WHERE namespace = ?", (namespace,)
    ).fetchone()

    if row is None:
        return NamespaceConfig(namespace=namespace)

    return NamespaceConfig(
        namespace=row["namespace"],
        vector_search_enabled=bool(row["vector_search_enabled"]),
        keyword_search_enabled=bool(row["keyword_search_enabled"]),
        output_fields=json.loads(row["output_fields"]),
    )


def upsert_namespace_config(
    conn: sqlite3.Connection,
    namespace: str,
    vector_search_enabled: bool | None = None,
    keyword_search_enabled: bool | None = None,
    output_fields: list[str] | None = None,
) -> NamespaceConfig:
    current = get_namespace_config(conn, namespace)

    updated = NamespaceConfig(
        namespace=namespace,
        vector_search_enabled=(
            current.vector_search_enabled
            if vector_search_enabled is None
            else vector_search_enabled
        ),
        keyword_search_enabled=(
            current.keyword_search_enabled
            if keyword_search_enabled is None
            else keyword_search_enabled
        ),
        output_fields=(
            current.output_fields if output_fields is None else output_fields
        ),
    )

    conn.execute(
        """
        INSERT INTO namespace_configs
            (namespace, vector_search_enabled, keyword_search_enabled, output_fields)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(namespace) DO UPDATE SET
            vector_search_enabled = excluded.vector_search_enabled,
            keyword_search_enabled = excluded.keyword_search_enabled,
            output_fields = excluded.output_fields
        """,
        (
            updated.namespace,
            int(updated.vector_search_enabled),
            int(updated.keyword_search_enabled),
            json.dumps(updated.output_fields),
        ),
    )

    return updated
