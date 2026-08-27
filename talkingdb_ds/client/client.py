import os
from typing import Any, Optional

import requests
from talkingdb.helpers.client import Config
from talkingdb.models.api.mode import ClientMode


class DSClient:
    """Dual-mode client for package-document-search.

    In DIRECT mode (default), calls the same service functions the API
    routers call, in-process - no network, no server needed. In API mode,
    calls a deployed package-document-search service over HTTP.

    ``DS_HOST`` is read locally rather than added to base-tdb-helpers'
    shared Config (matches package-parse-tree's PTClient / PT_HOST choice,
    for the same reason: avoid a cross-repo change per new client).
    """

    def __init__(self, config: Optional[Config] = None, headers: Optional[dict] = None):
        config = config or Config()
        self.mode = config.CLIENT_MODE
        self.timeout = config.API_TIMEOUT
        self.endpoint = os.getenv("DS_HOST")
        self.api_key = config.TDB_API_KEY

        self.session: Optional[requests.Session] = None
        if self.mode == ClientMode.API:
            if not self.endpoint:
                raise ValueError("DS_HOST is required in API mode")

            self.session = requests.Session()
            if self.api_key:
                self.session.headers["Authorization"] = f"Bearer {self.api_key}"
            if headers:
                self.session.headers.update(headers)

    # ------------------------------------------------------- knowledge base
    def list_namespaces(self) -> list[str]:
        if self.mode == ClientMode.API:
            return self._get("/api/namespaces")

        from talkingdb_ds.services.vector import store as vector_store

        return vector_store.list_namespaces()

    def create_namespace(
        self, namespace: str, description: Optional[str], field_schema: str
    ) -> list[str]:
        if self.mode == ClientMode.API:
            return self._post(
                f"/api/namespaces/{namespace}",
                {"description": description, "field_schema": field_schema},
            )

        from talkingdb_ds.services.vector import store as vector_store

        return vector_store.create_namespace(namespace, description, field_schema)

    def create_index(self, namespace: str, field: str) -> list[str]:
        if self.mode == ClientMode.API:
            return self._post(f"/api/namespaces/{namespace}/index", {"field": field})

        from talkingdb_ds.services.vector import store as vector_store

        vector_store.create_index(namespace, field)
        return vector_store.list_namespaces()

    # --------------------------------------------------------------- train
    def train_vectors(
        self,
        namespace: str,
        data: list[list],
        vector_index: int,
        partition: Optional[str] = None,
        update: bool = False,
    ) -> dict:
        if self.mode == ClientMode.API:
            return self._post(
                f"/api/namespaces/{namespace}/train/vectors",
                {
                    "data": data,
                    "vector_index": vector_index,
                    "partition": partition,
                    "update": update,
                },
            )

        from talkingdb_ds.services.train import trainer

        return trainer.train_vectors(
            namespace, data, vector_index, partition=partition, update=update
        )

    def train_keywords(
        self,
        namespace: str,
        documents: list[dict],
        id_field: str,
        partition: Optional[str] = None,
    ) -> dict:
        if self.mode == ClientMode.API:
            return self._post(
                f"/api/namespaces/{namespace}/train/keywords",
                {"documents": documents, "id_field": id_field, "partition": partition},
            )

        from talkingdb_ds.services.db import search_conn
        from talkingdb_ds.services.train import trainer

        count = trainer.index_keyword_documents(
            search_conn, namespace, documents, id_field, partition=partition
        )
        return {"namespace": namespace, "indexed": count}

    # -------------------------------------------------------------- search
    def search(
        self,
        namespace: str,
        query: str,
        vector_field: str,
        limit: int = 10,
        offset: int = 0,
        partition: Optional[str] = None,
        threshold: Optional[float] = None,
        filter_exp: str = "",
        keyword_field: Optional[str] = None,
    ) -> list[dict]:
        payload = {
            "query": query,
            "vector_field": vector_field,
            "limit": limit,
            "offset": offset,
            "partition": partition,
            "threshold": threshold,
            "filter_exp": filter_exp,
            "keyword_field": keyword_field,
        }
        if self.mode == ClientMode.API:
            return self._post(f"/api/namespaces/{namespace}/search", payload)

        from talkingdb_ds.services.db import search_conn
        from talkingdb_ds.services.search.orchestrator import search as run_search

        return run_search(
            search_conn,
            query=query,
            namespace=namespace,
            vector_field=vector_field,
            limit=limit,
            offset=offset,
            partition=partition,
            threshold=threshold,
            filter_exp=filter_exp,
            keyword_field=keyword_field,
        )

    # ------------------------------------------------------------- boundary
    def _post(self, path: str, json_body: Any) -> Any:
        response = self.session.post(
            f"{self.endpoint}{path}", json=json_body, timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def _get(self, path: str) -> Any:
        response = self.session.get(f"{self.endpoint}{path}", timeout=self.timeout)
        response.raise_for_status()
        return response.json()
