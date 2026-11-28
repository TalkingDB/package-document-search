<!-- short-readme -->
<h1 align="center">package-document-search</h1>

<p align="center"><b>Search documents by meaning and by exact words, in one ranked list.</b></p>

<p align="center"><a href="#try-it">Try it</a> · <a href="docs/architecture.md">How it works</a> · <a href="docs/usage-and-examples.md">Usage and examples</a> · <a href="docs/troubleshooting.md">Troubleshooting</a> · <a href="docs/reference.md">Full reference</a></p>

<p align="center"><a href="https://github.com/TalkingDB/package-document-search/stargazers"><img src="https://img.shields.io/github/stars/TalkingDB/package-document-search?style=social" alt="GitHub stars"></a></p>

<p align="center">
  <img src="docs/images/demo.gif" alt="Animated demo of a real run: a vector list and a keyword list are merged; BM25 ranks become match strengths, each document gets one fused score, and the best of both ranks first">
</p>
<p align="center"><sub>A real run of <code>talkingdb_ds/services/search/ranking.py</code> at <code>46c8d81</code> with Python 3.13.18, 26 Nov 2026.</sub></p>

One query runs as [vector search](https://en.wikipedia.org/wiki/Vector_database) in [Milvus](https://milvus.io/docs/overview.md) and as [BM25](https://en.wikipedia.org/wiki/Okapi_BM25) keyword search in SQLite FTS5; the two lists are fused, so a document found both ways ranks first.

## What it does

- **Index** text with embeddings and keywords ([how it works](docs/architecture.md)).
- **Search** both ways at once and fuse the scores ([example](docs/usage-and-examples.md)).
- **Test without a server**: [Milvus Lite](https://milvus.io/docs/milvus_lite.md) runs in a file.

## Try it

```bash
make sync MODE=git
poetry install
make test               # embedded Milvus Lite, no server needed
make local              # API on http://localhost:8094, Swagger at /docs
```

Indexing needs an `OPENAI_API_KEY` for embeddings.

## Where it fits

Fed by [package-search-trainer](https://github.com/TalkingDB/package-search-trainer); used by [module-ecommerce-ai](https://github.com/TalkingDB/module-ecommerce-ai) when a query names no category.

## Learn more

| Page | Read it to |
| :--- | :--- |
| [How it works](docs/architecture.md) | see the parts and how data moves |
| [Usage and examples](docs/usage-and-examples.md) | copy working examples |
| [Troubleshooting](docs/troubleshooting.md) | fix a problem |
| [Full reference](docs/reference.md) | read everything that used to be on this page |
| [All docs](docs/README.md) | see every page |

## Support TalkingDB

If package-document-search saved you time, please [give it a star](https://github.com/TalkingDB/package-document-search) ⭐. Stars help other developers find the project.

Found a bug, or a document it gets wrong? [Open an issue](https://github.com/TalkingDB/package-document-search/issues/new). We are always here to help and open to a conversation. Explore the TalkingDB applications at [talkingdb.io](https://talkingdb.io/#applications).

## License

> [!NOTE]
> This repository does not have a LICENSE file yet. Most TalkingDB repositories are licensed under [AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.html); until a LICENSE file is added here, no license is granted by this README.
