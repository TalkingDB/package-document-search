import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from talkingdb_ds.api.dependencies import get_search_conn
from talkingdb_ds.services.train import trainer

router = APIRouter(prefix="/api/namespaces/{namespace}", tags=["Training"])


class VectorTrainRequest(BaseModel):
    data: list[list]
    vector_index: int
    partition: str | None = None
    update: bool = False


class KeywordTrainRequest(BaseModel):
    documents: list[dict]
    id_field: str
    partition: str | None = None


@router.post("/train/vectors")
def train_vectors(namespace: str, request: VectorTrainRequest) -> dict:
    try:
        return trainer.train_vectors(
            namespace,
            request.data,
            request.vector_index,
            partition=request.partition,
            update=request.update,
        )
    except trainer.NamespaceNotRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"namespace '{exc}' not registered",
        ) from exc
    except trainer.EmptyEmbeddingValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.post("/train/keywords")
def train_keywords(
    namespace: str,
    request: KeywordTrainRequest,
    conn: sqlite3.Connection = Depends(get_search_conn),
) -> dict:
    count = trainer.index_keyword_documents(
        conn,
        namespace,
        request.documents,
        request.id_field,
        partition=request.partition,
    )
    return {"namespace": namespace, "indexed": count}
