import sqlite3

from talkingdb_ds.services.config.store import get_namespace_config
from talkingdb_ds.services.keyword import store as keyword_store
from talkingdb_ds.services.search.ranking import (
    combine_and_score_results,
    sort_and_filter_results_by_score,
)
from talkingdb_ds.services.vector import store as vector_store


def search(
    conn: sqlite3.Connection,
    query: str,
    namespace: str,
    vector_field: str,
    limit: int,
    offset: int = 0,
    partition: str | None = None,
    threshold: float | None = None,
    filter_exp: str = "",
    keyword_field: str | None = None,
) -> list[dict]:
    config = get_namespace_config(conn, namespace)

    vector_results = []
    if config.vector_search_enabled and namespace in vector_store.list_namespaces():
        vector_results = vector_store.search(
            query=query,
            namespace=namespace,
            vector_field=vector_field,
            output_fields=config.output_fields,
            limit=limit,
            offset=offset,
            filter_exp=filter_exp,
            threshold=threshold,
            partition=partition,
        )

    if not config.keyword_search_enabled or not keyword_field:
        return vector_results

    _, keyword_results = keyword_store.search(
        conn, query=query, namespace=namespace, field_name=keyword_field, limit=limit
    )

    combined = combine_and_score_results(vector_results, keyword_results)
    return sort_and_filter_results_by_score(combined)
