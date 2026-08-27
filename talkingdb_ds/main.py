from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from talkingdb_ds import __version__
from talkingdb_ds.api import kb, search, train

OPENAPI_TAGS = [
    {
        "name": "Knowledge Base",
        "description": "Managing namespaces, partitions, and vector indexes.",
    },
    {
        "name": "Training",
        "description": "Embedding and indexing documents for vector/keyword search.",
    },
    {
        "name": "Search",
        "description": "Hybrid vector + keyword search over a trained namespace.",
    },
]

app = FastAPI(
    title="TalkingDB Document Search",
    description=(
        "Hybrid vector + keyword document search: trains a per-namespace "
        "document index and serves ranked search results over it."
    ),
    version=__version__,
    openapi_tags=OPENAPI_TAGS,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kb.router)
app.include_router(train.router)
app.include_router(search.router)
