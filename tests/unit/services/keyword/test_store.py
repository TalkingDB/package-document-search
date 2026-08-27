from talkingdb_ds.services.keyword.store import (
    delete_document,
    index_document,
    search,
    tokenize,
)


def test_tokenize_splits_on_whitespace_and_punctuation():
    assert tokenize("red running shoes!") == ["red", "running", "shoes"]


def test_tokenize_keeps_hyphens_dots_and_numbers():
    assert tokenize("iphone-15 v1.2 model 3") == ["iphone-15", "v1.2", "model", "3"]


def test_index_and_search_document(search_conn):
    index_document(
        search_conn,
        "ns",
        "doc-1",
        {"title": "Red Running Shoes", "color": "red"},
    )

    tokens, results = search(search_conn, "running shoes", "ns", "title", limit=10)

    assert tokens == ["running", "shoes"]
    assert len(results) == 1
    assert results[0]["id"] == "doc-1"
    assert results[0]["title"] == "Red Running Shoes"


def test_search_returns_empty_for_stopword_only_query(search_conn):
    index_document(search_conn, "ns", "doc-1", {"title": "the a"})

    tokens, results = search(search_conn, "the a", "ns", "title", limit=10)

    assert tokens == []
    assert results == []


def test_search_scoped_by_namespace_and_field(search_conn):
    index_document(search_conn, "ns-a", "doc-1", {"title": "red shoes"})
    index_document(search_conn, "ns-b", "doc-2", {"title": "red shoes"})

    _, results = search(search_conn, "red shoes", "ns-a", "title", limit=10)

    assert [r["id"] for r in results] == ["doc-1"]


def test_reindexing_a_document_replaces_old_entry(search_conn):
    index_document(search_conn, "ns", "doc-1", {"title": "red shoes"})
    index_document(search_conn, "ns", "doc-1", {"title": "blue shoes"})

    _, results = search(search_conn, "red", "ns", "title", limit=10)
    assert results == []

    _, results = search(search_conn, "blue", "ns", "title", limit=10)
    assert len(results) == 1


def test_delete_document_removes_all_its_fields(search_conn):
    index_document(search_conn, "ns", "doc-1", {"title": "red shoes", "brand": "Acme"})

    delete_document(search_conn, "ns", "doc-1")

    _, results = search(search_conn, "red", "ns", "title", limit=10)
    assert results == []


def test_index_document_skips_empty_and_non_string_fields(search_conn):
    index_document(
        search_conn,
        "ns",
        "doc-1",
        {"title": "red shoes", "empty": "", "price": 50, "tags": None},
    )

    _, results = search(search_conn, "red", "ns", "title", limit=10)
    assert len(results) == 1
