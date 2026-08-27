# package-document-search

Hybrid vector plus keyword document search. Trains a per-namespace document
index and serves ranked search results over it, combining a vector similarity
score (via Milvus) with a keyword match score (via SQLite FTS5 and BM25
ranking).

This package is domain-agnostic TalkingDB infrastructure: it has no built-in
concept of "products," "ecommerce," or any other specific domain. Domain-specific
vocabulary and use cases (for example, ecommerce product search) are owned by
the `module-*` repos that consume this package, not by the package itself.

## Status

Core implementation complete: namespace/partition/index management, vector
training and search (Milvus), keyword training and search (SQLite FTS5), and
a hybrid ranking pipeline that combines both. Covered by a full test suite
that runs against an embedded Milvus Lite instance, no external Milvus server
required for tests (set `DS_MILVUS_URI` to point at a real or Lite instance;
production still uses `MILVUS_HOST`/`MILVUS_PORT` against a real server).

## Client

`talkingdb_ds.client.DSClient` gives callers a single interface that works two
ways, controlled by the `CLIENT_MODE` env var (defaults to `direct`):

- **DIRECT mode**: calls the same service functions the API routers call,
  in-process.
- **API mode**: calls a deployed package-document-search service over HTTP.
  Set `CLIENT_MODE=api` and `DS_HOST` to the deployed base URL.

## Development

```
make sync MODE=git      # or MODE=local for editable base-tdb-* checkouts
poetry install
make test
make local               # run with hot reload
```

See `Makefile` for the full list of targets.
