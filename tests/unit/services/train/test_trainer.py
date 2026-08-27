import json

import pytest

from talkingdb_ds.services.train import trainer
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


def test_train_vectors_raises_for_unregistered_namespace():
    with pytest.raises(trainer.NamespaceNotRegisteredError):
        trainer.train_vectors(
            "does-not-exist", [["id-1"], ["some text"]], vector_index=1
        )


def test_train_vectors_raises_for_empty_embedding_value(namespace, field_schema):
    vector_store.create_namespace(namespace, "test", field_schema)

    with pytest.raises(trainer.EmptyEmbeddingValueError):
        trainer.train_vectors(namespace, [["id-1"], [""]], vector_index=1)


def test_train_vectors_embeds_and_inserts(namespace, field_schema, monkeypatch):
    vector_store.create_namespace(namespace, "test", field_schema)
    vector_store.create_index(namespace, "embedding")
    monkeypatch.setattr(
        "talkingdb_ds.services.train.trainer.create_embeddings",
        lambda values: [[0.33541] * 8 for _ in values],
    )

    result = trainer.train_vectors(
        namespace,
        [["shoe-1"], ["Red Running Shoes"], ["Red Running Shoes"]],
        vector_index=1,
    )

    assert result == {namespace: 1}


def test_index_keyword_documents_returns_count(search_conn):
    documents = [
        {"sku": "shoe-1", "title": "Red Running Shoes"},
        {"sku": "shoe-2", "title": "Blue Walking Shoes"},
    ]

    count = trainer.index_keyword_documents(
        search_conn, "ns", documents, id_field="sku"
    )

    assert count == 2
