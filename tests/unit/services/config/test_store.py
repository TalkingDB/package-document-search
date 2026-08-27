from talkingdb_ds.services.config.store import (
    get_namespace_config,
    upsert_namespace_config,
)


def test_get_config_defaults_when_never_set(search_conn):
    config = get_namespace_config(search_conn, "ns")

    assert config.namespace == "ns"
    assert config.vector_search_enabled is True
    assert config.keyword_search_enabled is True
    assert config.output_fields == []


def test_upsert_creates_and_persists(search_conn):
    upsert_namespace_config(
        search_conn,
        "ns",
        vector_search_enabled=False,
        output_fields=["title", "price"],
    )

    config = get_namespace_config(search_conn, "ns")
    assert config.vector_search_enabled is False
    assert config.keyword_search_enabled is True
    assert config.output_fields == ["title", "price"]


def test_upsert_partial_update_preserves_other_fields(search_conn):
    upsert_namespace_config(
        search_conn, "ns", vector_search_enabled=False, output_fields=["title"]
    )

    upsert_namespace_config(search_conn, "ns", keyword_search_enabled=False)

    config = get_namespace_config(search_conn, "ns")
    assert config.vector_search_enabled is False
    assert config.keyword_search_enabled is False
    assert config.output_fields == ["title"]
