def _normalize_keyword_matches(keyword_results: list[dict]) -> dict[str, float]:
    """Map each keyword hit's id to a 0..1 match strength, derived from its
    FTS5 bm25 rank (more negative = stronger match) relative to the best and
    worst ranks in this result set."""

    if not keyword_results:
        return {}

    ranks = [r["rank"] for r in keyword_results]
    best, worst = min(ranks), max(ranks)
    spread = worst - best

    def strength(rank: float) -> float:
        return 1.0 if spread == 0 else round((worst - rank) / spread, 3)

    return {r["id"]: strength(r["rank"]) for r in keyword_results}


def combine_and_score_results(
    vector_results: list[dict], keyword_results: list[dict]
) -> list[dict]:
    match_strength = _normalize_keyword_matches(keyword_results)
    keyword_by_id = {r["id"]: r for r in keyword_results}
    combined = []
    seen = set()

    for item in vector_results:
        score = 2.0
        if item["id"] in keyword_by_id:
            score += match_strength[item["id"]]
            combined.append({**keyword_by_id[item["id"]], **item, "score": score})
        else:
            combined.append({**item, "score": score})
        seen.add(item["id"])

    for doc_id, item in keyword_by_id.items():
        if doc_id in seen:
            continue
        combined.append({**item, "score": 1.0 + match_strength[doc_id]})

    return combined


def sort_and_filter_results_by_score(results: list[dict]) -> list[dict]:
    filtered = [r for r in results if r["score"] > 1]
    return sorted(filtered, key=lambda r: r["score"], reverse=True)
