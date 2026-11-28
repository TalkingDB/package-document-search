# Troubleshooting

[Docs home](README.md) › Troubleshooting

| Symptom | Likely cause | Fix |
| :--- | :--- | :--- |
| Connection refused to `milvus-db:19530` | No Milvus server; `MILVUS_HOST` defaults to a [Docker](https://docs.docker.com/get-started/docker-overview/) service name | Run Milvus, set `MILVUS_HOST` and `MILVUS_PORT`, or set `DS_MILVUS_URI` to a Milvus Lite file for local work |
| `openai.AuthenticationError` or a missing key error during training or search | `OPENAI_API_KEY` is not set | Set it in the service environment. Vector training and vector search both need it |
| Training fails with "[embeddings](https://en.wikipedia.org/wiki/Word_embedding) operation cannot run on empty strings" | A value in the `vector_index` column is empty | Remove or fill empty texts before training |
| Training rejects the namespace as not registered | The namespace was never created in Milvus | `POST /api/namespaces/{namespace}` with a `field_schema` first |
| Milvus rejects the insert: wrong number of fields or dimension | `data` is not column by column in schema order, or `dim` does not match the embedding size | Send one list per field in schema order; use `dim` 1536 for `text-embedding-ada-002` |
| Search returns `[]` for a new namespace | Nothing was trained yet, or the namespace is missing in Milvus | Train vectors and keywords, then search again |
| Relevant documents are missing from vector results | Their similarity is at or below the cutoff, 0.70 by default | Pass a lower `threshold` in the search request |
| Keyword matches never show up | No `keyword_field` in the search request, or keyword search is switched off in the namespace config | Pass `keyword_field`; check `GET /api/namespaces/{namespace}/config` |
| A keyword match you expected is missing | The weakest keyword only hit in each search scores 1.0 and is dropped by design | Widen the query, or raise `limit` so more keyword hits compete |
| Results look unordered among vector hits | Every vector hit starts at score 2.0 | Use `threshold` to remove weak vector matches; see [the scoring rule](architecture.md#the-scoring-rule) |
| `ModuleNotFoundError: No module named 'talkingdb'` | `base-tdb-*` not installed | `make sync MODE=git && poetry install` |

---

**Related:** [Architecture](architecture.md) · [Usage and examples](usage-and-examples.md) · [README](../README.md)
