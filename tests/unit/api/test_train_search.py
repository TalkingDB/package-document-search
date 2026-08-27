import json
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from talkingdb_ds.main import app

client = TestClient(app)


@pytest.fixture
def namespace():
    return f"test_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def field_schema():
    return json.dumps(
        [
            {"name": "id", "dtype": "string", "is_primary": True, "max_length": 64},
            {"name": "embedding", "dtype": "vector", "dim": 8},
            {"name": "title", "dtype": "string", "max_length": 256},
        ]
    )


def _create_namespace(namespace, field_schema):
    client.post(
        f"/api/namespaces/{namespace}",
        json={"description": "test", "field_schema": field_schema},
    )
    client.post(f"/api/namespaces/{namespace}/index", json={"field": "embedding"})


def test_train_vectors_404_for_unregistered_namespace():
    response = client.post(
        "/api/namespaces/does-not-exist/train/vectors",
        json={"data": [["id-1"], ["text"]], "vector_index": 1},
    )
    assert response.status_code == 404


def test_train_vectors_400_for_empty_embedding_value(namespace, field_schema):
    _create_namespace(namespace, field_schema)

    response = client.post(
        f"/api/namespaces/{namespace}/train/vectors",
        json={"data": [["id-1"], [""]], "vector_index": 1},
    )
    assert response.status_code == 400


def test_train_keywords_and_search_end_to_end(namespace, field_schema):
    _create_namespace(namespace, field_schema)

    with patch(
        "talkingdb_ds.services.train.trainer.create_embeddings",
        return_value=[[0.33541] * 8],
    ):
        train_response = client.post(
            f"/api/namespaces/{namespace}/train/vectors",
            json={
                "data": [["shoe-1"], ["Red Running Shoes"], ["Red Running Shoes"]],
                "vector_index": 1,
            },
        )
    assert train_response.status_code == 200
    assert train_response.json() == {namespace: 1}

    keyword_response = client.post(
        f"/api/namespaces/{namespace}/train/keywords",
        json={
            "documents": [{"sku": "shoe-1", "title": "Red Running Shoes"}],
            "id_field": "sku",
        },
    )
    assert keyword_response.status_code == 200
    assert keyword_response.json() == {"namespace": namespace, "indexed": 1}

    client.put(f"/api/namespaces/{namespace}/config", json={"output_fields": ["title"]})

    with patch(
        "talkingdb_ds.services.vector.store.create_embedding",
        return_value=[0.33541] * 8,
    ):
        search_response = client.post(
            f"/api/namespaces/{namespace}/search",
            json={
                "query": "red running shoes",
                "vector_field": "embedding",
                "keyword_field": "title",
            },
        )

    assert search_response.status_code == 200
    body = search_response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Red Running Shoes"


def test_get_and_update_config(namespace, field_schema):
    _create_namespace(namespace, field_schema)

    response = client.get(f"/api/namespaces/{namespace}/config")
    assert response.json()["vector_search_enabled"] is True

    response = client.put(
        f"/api/namespaces/{namespace}/config", json={"vector_search_enabled": False}
    )
    assert response.json()["vector_search_enabled"] is False
