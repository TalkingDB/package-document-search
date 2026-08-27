from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from talkingdb_ds.services.vector import store as vector_store

router = APIRouter(prefix="/api/namespaces", tags=["Knowledge Base"])


class NamespaceCreate(BaseModel):
    description: str | None = None
    field_schema: str


class PartitionCreate(BaseModel):
    name: str
    description: str | None = None


class IndexCreate(BaseModel):
    field: str


class VectorIds(BaseModel):
    vector_ids: list[str]


def _not_found(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("")
def list_namespaces() -> list[str]:
    return vector_store.list_namespaces()


@router.post("/{namespace}")
def create_namespace(namespace: str, request: NamespaceCreate) -> list[str]:
    return vector_store.create_namespace(
        namespace, request.description, request.field_schema
    )


@router.delete("/{namespace}")
def delete_namespace(namespace: str) -> dict:
    try:
        vector_store.delete_namespace(namespace)
    except vector_store.NamespaceNotFoundError as exc:
        raise _not_found(exc) from exc
    return {"namespace": namespace, "deleted": True}


@router.get("/{namespace}/partitions")
def list_partitions(namespace: str) -> dict:
    try:
        return vector_store.list_partitions(namespace)
    except vector_store.NamespaceNotFoundError as exc:
        raise _not_found(exc) from exc


@router.post("/{namespace}/partitions")
def create_partition(namespace: str, request: PartitionCreate) -> dict:
    try:
        return vector_store.create_partition(
            namespace, request.name, request.description
        )
    except vector_store.NamespaceNotFoundError as exc:
        raise _not_found(exc) from exc


@router.delete("/{namespace}/partitions/{partition}")
def delete_partition(namespace: str, partition: str) -> dict:
    try:
        vector_store.delete_partition(namespace, partition)
    except (
        vector_store.NamespaceNotFoundError,
        vector_store.PartitionNotFoundError,
    ) as exc:
        raise _not_found(exc) from exc
    return {"namespace": namespace, "partition": partition, "deleted": True}


@router.delete("/{namespace}/partitions/{partition}/vectors")
def delete_partition_vectors(
    namespace: str, partition: str, request: VectorIds
) -> dict:
    vector_store.delete_vectors(namespace, partition, request.vector_ids)
    return {
        "namespace": namespace,
        "partition": partition,
        "deleted": len(request.vector_ids),
    }


@router.post("/{namespace}/index")
def create_index(namespace: str, request: IndexCreate) -> list[str]:
    try:
        vector_store.create_index(namespace, request.field)
    except vector_store.NamespaceNotFoundError as exc:
        raise _not_found(exc) from exc
    return vector_store.list_namespaces()
