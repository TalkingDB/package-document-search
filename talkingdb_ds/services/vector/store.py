import json
import os

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    Partition,
    connections,
    utility,
)

from talkingdb_ds.services.vector.embeddings import create_embedding

MILVUS_HOST = os.getenv("MILVUS_HOST", "milvus-db")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
# Set for local/test use (e.g. a Milvus Lite file path) to connect without a
# live Milvus server. Takes precedence over MILVUS_HOST/MILVUS_PORT.
DS_MILVUS_URI = os.getenv("DS_MILVUS_URI")

_DTYPE_MAPPINGS = {
    "int": DataType.INT64,
    "string": DataType.VARCHAR,
    "vector": DataType.FLOAT_VECTOR,
}

_INDEX_PARAMS = {
    "index_type": "IVF_FLAT",
    "metric_type": "IP",
    "params": {"nlist": 1024},
}

_connected = False
_collection_cache: dict[str, Collection] = {}


def _ensure_connected() -> None:
    global _connected

    if not _connected:
        if DS_MILVUS_URI:
            connections.connect(uri=DS_MILVUS_URI)
        else:
            connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        _connected = True


class NamespaceNotFoundError(Exception):
    pass


class PartitionNotFoundError(Exception):
    pass


def list_namespaces() -> list[str]:
    _ensure_connected()
    return utility.list_collections()


def create_namespace(name: str, description: str, field_schema: str) -> list[str]:
    _ensure_connected()

    if name not in list_namespaces():
        fields = []

        for field_info in json.loads(field_schema):
            field_info = {**field_info, "dtype": _DTYPE_MAPPINGS[field_info["dtype"]]}
            fields.append(FieldSchema(**field_info))

        schema = CollectionSchema(fields=fields, description=description)
        Collection(name=name, schema=schema)

    return list_namespaces()


def delete_namespace(namespace: str) -> None:
    _ensure_connected()

    if namespace not in list_namespaces():
        raise NamespaceNotFoundError(namespace)

    utility.drop_collection(namespace)
    _collection_cache.pop(namespace, None)


def list_partitions(namespace: str) -> dict[str, dict]:
    _ensure_connected()

    if namespace not in list_namespaces():
        raise NamespaceNotFoundError(namespace)

    collection = Collection(namespace)

    return {
        p.name: {"entities": p.num_entities, "description": p.description}
        for p in collection.partitions
        if p.name != "_default"
    }


def create_partition(namespace: str, name: str, description: str) -> dict[str, dict]:
    _ensure_connected()

    if namespace not in list_namespaces():
        raise NamespaceNotFoundError(namespace)

    collection = Collection(namespace)

    if name not in list_partitions(namespace):
        collection.create_partition(name, description)

    return list_partitions(namespace)


def delete_partition(namespace: str, name: str) -> None:
    _ensure_connected()

    if namespace not in list_namespaces():
        raise NamespaceNotFoundError(namespace)

    if name not in list_partitions(namespace):
        raise PartitionNotFoundError(name)

    collection = Collection(namespace)
    partition = Partition(collection, name)
    collection.release()
    partition.release()
    partition.drop()


def create_index(namespace: str, field: str) -> None:
    _ensure_connected()

    if namespace not in list_namespaces():
        raise NamespaceNotFoundError(namespace)

    Collection(namespace).create_index(field_name=field, index_params=_INDEX_PARAMS)


def _get_collection(namespace: str) -> Collection:
    if namespace not in _collection_cache:
        collection = Collection(namespace)
        collection.load()
        _collection_cache[namespace] = collection

    return _collection_cache[namespace]


def _sanitize(data):
    if data is None:
        return ""
    if isinstance(data, dict):
        return {k: _sanitize(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_sanitize(v) for v in data]
    return data


def namespace_entity_count(namespace: str) -> dict:
    return {namespace: Collection(namespace).num_entities}


def insert(namespace: str, bulk_data: list, partition: str | None = None) -> None:
    _ensure_connected()

    collection = Collection(namespace)

    if partition:
        if partition not in list_partitions(namespace):
            raise PartitionNotFoundError(partition)
        collection.insert(data=bulk_data, partition_name=partition)
    else:
        collection.insert(bulk_data)


def upsert(namespace: str, data: list, partition: str) -> None:
    _ensure_connected()

    if partition not in list_partitions(namespace):
        raise PartitionNotFoundError(partition)

    Collection(namespace).upsert(data=_sanitize(data), partition_name=partition)


def delete_vectors(namespace: str, partition: str, vector_ids: list[str]) -> None:
    _ensure_connected()

    ids = ",".join(f"'{v}'" for v in vector_ids)
    Collection(namespace).delete(f"id in [{ids}]", partition_name=partition)


def _rows_from_hits(hits, output_fields: list[str]) -> list[dict]:
    return [
        {
            "id": hit.id,
            "score": hit.distance,
            **{field: hit.entity.get(field) for field in output_fields},
        }
        for hit in hits
    ]


def search(
    query: str,
    namespace: str,
    vector_field: str,
    output_fields: list[str],
    limit: int,
    offset: int,
    filter_exp: str,
    threshold: float | None,
    partition: str | None = None,
) -> list[dict]:
    _ensure_connected()

    embedding = create_embedding(query)
    search_params = {"metric_type": "IP", "radius": 0.70, "range_filter": 1.0}

    if partition:
        collection = Collection(namespace)
        collection.load()
        target = Partition(collection, partition)
    else:
        target = _get_collection(namespace)

    results = target.search(
        data=[embedding],
        anns_field=vector_field,
        param=search_params,
        limit=limit,
        offset=offset,
        output_fields=output_fields,
        expr=filter_exp,
    )

    rows = _rows_from_hits(results[0], output_fields)
    cutoff = threshold if threshold else 0.70

    return [row for row in rows if round(row["score"], 3) > cutoff]
