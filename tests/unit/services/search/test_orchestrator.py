import json

import pytest

from talkingdb_ds.services.keyword.store import index_document
from talkingdb_ds.services.search.orchestrator import search
from talkingdb_ds.services.train.trainer import train_vectors
from talkingdb_ds.services.vector import store as vector_store


@pytest.fixture
def field_schema():
    return json.dumps(
        [
            {"name": "id", "dtype": "string", "is_primary": True, "max_length": 64},
            {"name": "embedding", "dtype": "vector", "dim": 8},
            {"name": "title", "dtype": "string", "max_length": 256},
        ]
    )


def test_search_returns_empty_when_namespace_never_trained(search_conn, namespace):
    results = search(
        search_conn,
        query="red shoes",
        namespace=namespace,
        vector_field="embedding",
        limit=10,
    )

    assert results == []


def test_search_vector_only_when_no_keyword_field(
    search_conn, namespace, field_schema, monkeypatch
):
    from talkingdb_ds.services.config.store import upsert_namespace_config

    vector_store.create_namespace(namespace, "test", field_schema)
    vector_store.create_index(namespace, "embedding")
    upsert_namespace_config(search_conn, namespace, output_fields=["title"])
    monkeypatch.setattr(
        "talkingdb_ds.services.train.trainer.create_embeddings",
        lambda values: [[0.33541] * 8 for _ in values],
    )
    monkeypatch.setattr(
        "talkingdb_ds.services.vector.store.create_embedding",
        lambda text: [0.33541] * 8,
    )
    train_vectors(
        namespace, [["shoe-1"], ["Red Running Shoes"], ["Red Running Shoes"]], 1
    )

    results = search(
        search_conn,
        query="red shoes",
        namespace=namespace,
        vector_field="embedding",
        limit=10,
    )

    assert len(results) == 1
    assert results[0]["title"] == "Red Running Shoes"


def test_search_combines_vector_and_keyword_hits(
    search_conn, namespace, field_schema, monkeypatch
):
    vector_store.create_namespace(namespace, "test", field_schema)
    vector_store.create_index(namespace, "embedding")
    monkeypatch.setattr(
        "talkingdb_ds.services.train.trainer.create_embeddings",
        lambda values: [[0.33541] * 8 for _ in values],
    )
    monkeypatch.setattr(
        "talkingdb_ds.services.vector.store.create_embedding",
        lambda text: [0.33541] * 8,
    )
    train_vectors(
        namespace, [["shoe-1"], ["Red Running Shoes"], ["Red Running Shoes"]], 1
    )
    index_document(search_conn, namespace, "shoe-1", {"title": "Red Running Shoes"})

    results = search(
        search_conn,
        query="red running shoes",
        namespace=namespace,
        vector_field="embedding",
        limit=10,
        keyword_field="title",
    )

    assert len(results) == 1
    assert results[0]["id"] == "shoe-1"
    assert results[0]["score"] > 2.0  # boosted by matching both vector and keyword


def test_search_respects_vector_search_disabled_config(
    search_conn, namespace, field_schema, monkeypatch
):
    from talkingdb_ds.services.config.store import upsert_namespace_config

    vector_store.create_namespace(namespace, "test", field_schema)
    vector_store.create_index(namespace, "embedding")
    monkeypatch.setattr(
        "talkingdb_ds.services.train.trainer.create_embeddings",
        lambda values: [[0.33541] * 8 for _ in values],
    )
    train_vectors(
        namespace, [["shoe-1"], ["Red Running Shoes"], ["Red Running Shoes"]], 1
    )
    index_document(search_conn, namespace, "shoe-1", {"title": "Red Running Shoes"})
    upsert_namespace_config(search_conn, namespace, vector_search_enabled=False)

    results = search(
        search_conn,
        query="red running shoes",
        namespace=namespace,
        vector_field="embedding",
        limit=10,
        keyword_field="title",
    )

    # vector disabled -> only the keyword hit. A sole keyword match gets
    # full match strength (1.0), scoring 2.0 same as a vector-only hit -
    # the two paths aren't distinguishable by score alone here, so check
    # the vector output field is genuinely absent instead.
    assert len(results) == 1
    assert "embedding" not in results[0]
