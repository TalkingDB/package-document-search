import pytest

from talkingdb_ds.services.vector import store as vector_store


@pytest.fixture
def field_schema():
    import json

    return json.dumps(
        [
            {"name": "id", "dtype": "string", "is_primary": True, "max_length": 64},
            {"name": "embedding", "dtype": "vector", "dim": 8},
            {"name": "title", "dtype": "string", "max_length": 256},
        ]
    )


def test_create_and_list_namespace(namespace, field_schema):
    names = vector_store.create_namespace(namespace, "test collection", field_schema)

    assert namespace in names
    assert namespace in vector_store.list_namespaces()


def test_create_namespace_is_idempotent(namespace, field_schema):
    vector_store.create_namespace(namespace, "test collection", field_schema)
    names = vector_store.create_namespace(namespace, "test collection", field_schema)

    assert names.count(namespace) == 1


def test_delete_namespace(namespace, field_schema):
    vector_store.create_namespace(namespace, "test collection", field_schema)

    vector_store.delete_namespace(namespace)

    assert namespace not in vector_store.list_namespaces()


def test_delete_namespace_raises_when_missing():
    with pytest.raises(vector_store.NamespaceNotFoundError):
        vector_store.delete_namespace("does-not-exist")


def test_create_and_list_partitions(namespace, field_schema):
    vector_store.create_namespace(namespace, "test collection", field_schema)

    partitions = vector_store.create_partition(namespace, "us", "US catalog")

    assert "us" in partitions
    assert partitions["us"]["entities"] == 0


def test_create_partition_raises_for_missing_namespace():
    with pytest.raises(vector_store.NamespaceNotFoundError):
        vector_store.create_partition("does-not-exist", "us", "desc")


def test_insert_and_search_round_trip(namespace, field_schema, monkeypatch):
    vector_store.create_namespace(namespace, "test collection", field_schema)
    vector_store.create_index(namespace, "embedding")

    monkeypatch.setattr(
        "talkingdb_ds.services.vector.store.create_embedding",
        lambda text: [0.33541] * 8,
    )

    vector_store.insert(
        namespace,
        bulk_data=[["shoe-1"], [[0.33541] * 8], ["Red Running Shoes"]],
    )

    results = vector_store.search(
        query="running shoes",
        namespace=namespace,
        vector_field="embedding",
        output_fields=["title"],
        limit=10,
        offset=0,
        filter_exp="",
        threshold=0.0,
    )

    assert len(results) == 1
    assert results[0]["title"] == "Red Running Shoes"


def test_namespace_entity_count(namespace, field_schema, monkeypatch):
    vector_store.create_namespace(namespace, "test collection", field_schema)
    vector_store.create_index(namespace, "embedding")
    monkeypatch.setattr(
        "talkingdb_ds.services.vector.store.create_embedding",
        lambda text: [0.33541] * 8,
    )

    vector_store.insert(
        namespace, bulk_data=[["shoe-1"], [[0.33541] * 8], ["Red Running Shoes"]]
    )

    assert vector_store.namespace_entity_count(namespace) == {namespace: 1}
