import json
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from talkingdb.models.api.mode import ClientMode

from talkingdb_ds.client import DSClient


def direct_config():
    return SimpleNamespace(
        CLIENT_MODE=ClientMode.DIRECT, API_TIMEOUT=30, TDB_API_KEY=None
    )


def api_config(api_key=None):
    return SimpleNamespace(
        CLIENT_MODE=ClientMode.API, API_TIMEOUT=30, TDB_API_KEY=api_key
    )


@pytest.fixture
def namespace():
    return f"client_test_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def field_schema():
    return json.dumps(
        [
            {"name": "id", "dtype": "string", "is_primary": True, "max_length": 64},
            {"name": "embedding", "dtype": "vector", "dim": 8},
            {"name": "title", "dtype": "string", "max_length": 256},
        ]
    )


class TestDirectMode:
    def test_namespace_and_index_roundtrip(self, namespace, field_schema):
        client = DSClient(config=direct_config())

        names = client.create_namespace(namespace, "test", field_schema)
        assert namespace in names

        names = client.create_index(namespace, "embedding")
        assert namespace in names
        assert namespace in client.list_namespaces()

    def test_train_and_search_round_trip(self, namespace, field_schema):
        client = DSClient(config=direct_config())
        client.create_namespace(namespace, "test", field_schema)
        client.create_index(namespace, "embedding")

        with patch(
            "talkingdb_ds.services.train.trainer.create_embeddings",
            return_value=[[0.33541] * 8],
        ):
            result = client.train_vectors(
                namespace,
                [["shoe-1"], ["Red Running Shoes"], ["Red Running Shoes"]],
                vector_index=1,
            )
        assert result == {namespace: 1}

        indexed = client.train_keywords(
            namespace, [{"sku": "shoe-1", "title": "Red Running Shoes"}], id_field="sku"
        )
        assert indexed == {"namespace": namespace, "indexed": 1}

        with patch(
            "talkingdb_ds.services.vector.store.create_embedding",
            return_value=[0.33541] * 8,
        ):
            results = client.search(
                namespace,
                query="red running shoes",
                vector_field="embedding",
                keyword_field="title",
            )

        assert len(results) == 1
        assert results[0]["id"] == "shoe-1"


class TestApiMode:
    def test_requires_ds_host(self):
        with pytest.raises(ValueError, match="DS_HOST"):
            DSClient(config=api_config())

    def test_search_posts_to_configured_host(self, monkeypatch):
        monkeypatch.setenv("DS_HOST", "http://ds.internal")
        client = DSClient(config=api_config(api_key="secret"))

        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = [{"id": "shoe-1"}]
        client.session.post = MagicMock(return_value=fake_response)

        result = client.search("acme", query="red shoes", vector_field="embedding")

        assert result == [{"id": "shoe-1"}]
        client.session.post.assert_called_once_with(
            "http://ds.internal/api/namespaces/acme/search",
            json={
                "query": "red shoes",
                "vector_field": "embedding",
                "limit": 10,
                "offset": 0,
                "partition": None,
                "threshold": None,
                "filter_exp": "",
                "keyword_field": None,
            },
            timeout=30,
        )
        assert client.session.headers["Authorization"] == "Bearer secret"

    def test_list_namespaces_gets_configured_host(self, monkeypatch):
        monkeypatch.setenv("DS_HOST", "http://ds.internal")
        client = DSClient(config=api_config())

        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = ["acme"]
        client.session.get = MagicMock(return_value=fake_response)

        assert client.list_namespaces() == ["acme"]
        client.session.get.assert_called_once_with(
            "http://ds.internal/api/namespaces", timeout=30
        )
