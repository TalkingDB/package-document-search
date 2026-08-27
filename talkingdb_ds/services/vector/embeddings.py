from openai import OpenAI

from talkingdb_ds.services.utils import create_batches

EMBEDDING_MODEL = "text-embedding-ada-002"

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client

    if _client is None:
        _client = OpenAI()

    return _client


def create_embeddings(values: list[str]) -> list[list[float]]:
    embeddings = []

    for batch in create_batches(values, division_factor=2):
        response = _get_client().embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
            encoding_format="float",
        )
        embeddings.extend(d.embedding for d in response.data)

    return embeddings


def create_embedding(value: str) -> list[float]:
    return create_embeddings([value])[0]
