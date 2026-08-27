import json
import uuid

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
        ]
    )


def test_create_and_list_namespace(namespace, field_schema):
    response = client.post(
        f"/api/namespaces/{namespace}",
        json={"description": "test", "field_schema": field_schema},
    )
    assert response.status_code == 200
    assert namespace in response.json()

    response = client.get("/api/namespaces")
    assert namespace in response.json()


def test_delete_namespace_404_when_missing():
    response = client.delete("/api/namespaces/does-not-exist")
    assert response.status_code == 404


def test_create_and_list_partitions(namespace, field_schema):
    client.post(
        f"/api/namespaces/{namespace}",
        json={"description": "test", "field_schema": field_schema},
    )

    response = client.post(
        f"/api/namespaces/{namespace}/partitions",
        json={"name": "us", "description": "US catalog"},
    )
    assert response.status_code == 200
    assert "us" in response.json()

    response = client.get(f"/api/namespaces/{namespace}/partitions")
    assert "us" in response.json()


def test_create_partition_404_for_missing_namespace():
    response = client.post(
        "/api/namespaces/does-not-exist/partitions",
        json={"name": "us", "description": "desc"},
    )
    assert response.status_code == 404
