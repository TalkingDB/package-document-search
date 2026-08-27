import sqlite3

from talkingdb_ds.services.keyword import store as keyword_store
from talkingdb_ds.services.vector import store as vector_store
from talkingdb_ds.services.vector.embeddings import create_embeddings


class EmptyEmbeddingValueError(Exception):
    pass


class NamespaceNotRegisteredError(Exception):
    pass


def train_vectors(
    namespace: str,
    data: list[list],
    vector_index: int,
    partition: str | None = None,
    update: bool = False,
) -> dict:
    if namespace not in vector_store.list_namespaces():
        raise NamespaceNotRegisteredError(namespace)

    to_embed = data[vector_index]

    if any(len(v) == 0 for v in to_embed):
        raise EmptyEmbeddingValueError(
            "embeddings operation cannot run on empty strings"
        )

    data = [*data]
    data[vector_index] = create_embeddings(to_embed)

    if not partition:
        vector_store.insert(namespace, bulk_data=data)
    elif not update:
        vector_store.insert(namespace, bulk_data=data, partition=partition)
    else:
        vector_store.upsert(namespace, data=data, partition=partition)

    return vector_store.namespace_entity_count(namespace)


def index_keyword_documents(
    conn: sqlite3.Connection,
    namespace: str,
    documents: list[dict],
    id_field: str,
    partition: str | None = None,
) -> int:
    for doc in documents:
        keyword_store.index_document(
            conn, namespace, doc_id=str(doc[id_field]), fields=doc, partition=partition
        )

    return len(documents)
