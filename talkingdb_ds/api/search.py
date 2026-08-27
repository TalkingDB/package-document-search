import sqlite3

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from talkingdb_ds.api.dependencies import get_search_conn
from talkingdb_ds.services.config.store import NamespaceConfig, upsert_namespace_config
from talkingdb_ds.services.config.store import (
    get_namespace_config as _get_namespace_config,
)
from talkingdb_ds.services.search.orchestrator import search as run_search

router = APIRouter(prefix="/api/namespaces/{namespace}", tags=["Search"])


class SearchRequest(BaseModel):
    query: str
    vector_field: str
    limit: int = 10
    offset: int = 0
    partition: str | None = None
    threshold: float | None = None
    filter_exp: str = ""
    keyword_field: str | None = None


class ConfigUpdate(BaseModel):
    vector_search_enabled: bool | None = None
    keyword_search_enabled: bool | None = None
    output_fields: list[str] | None = None


@router.post("/search")
def search(
    namespace: str,
    request: SearchRequest,
    conn: sqlite3.Connection = Depends(get_search_conn),
) -> list[dict]:
    return run_search(
        conn,
        query=request.query,
        namespace=namespace,
        vector_field=request.vector_field,
        limit=request.limit,
        offset=request.offset,
        partition=request.partition,
        threshold=request.threshold,
        filter_exp=request.filter_exp,
        keyword_field=request.keyword_field,
    )


@router.get("/config")
def get_config(
    namespace: str, conn: sqlite3.Connection = Depends(get_search_conn)
) -> NamespaceConfig:
    return _get_namespace_config(conn, namespace)


@router.put("/config")
def update_config(
    namespace: str,
    request: ConfigUpdate,
    conn: sqlite3.Connection = Depends(get_search_conn),
) -> NamespaceConfig:
    return upsert_namespace_config(
        conn,
        namespace,
        vector_search_enabled=request.vector_search_enabled,
        keyword_search_enabled=request.keyword_search_enabled,
        output_fields=request.output_fields,
    )
