DEFAULT_EMBEDDING_BATCH_SIZE = 100


def create_batches(
    items: list,
    batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
    division_factor: int = 1,
) -> list[list]:
    size = max(1, batch_size // division_factor)
    return [items[i : i + size] for i in range(0, len(items), size)]
