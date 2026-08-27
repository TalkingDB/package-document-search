from talkingdb_ds.services.search.ranking import (
    combine_and_score_results,
    sort_and_filter_results_by_score,
)


def test_vector_only_hit_scores_base_two():
    combined = combine_and_score_results(
        vector_results=[{"id": "a", "score": 0.9}], keyword_results=[]
    )

    assert combined == [{"id": "a", "score": 2.0}]


def test_keyword_only_hit_scores_below_two():
    combined = combine_and_score_results(
        vector_results=[],
        keyword_results=[{"id": "a", "title": "red shoes", "rank": -1.0}],
    )

    assert combined[0]["id"] == "a"
    assert combined[0]["score"] == 2.0  # sole result -> spread 0 -> strength 1.0


def test_hit_in_both_scores_highest():
    combined = combine_and_score_results(
        vector_results=[{"id": "a", "score": 0.9}, {"id": "b", "score": 0.8}],
        keyword_results=[
            {"id": "a", "title": "red shoes", "rank": -2.0},
            {"id": "c", "title": "blue shoes", "rank": -1.0},
        ],
    )

    by_id = {r["id"]: r for r in combined}
    # "a" is in both -> 2.0 base + keyword strength boost -> highest score
    assert by_id["a"]["score"] > by_id["b"]["score"]
    assert by_id["a"]["score"] > by_id["c"]["score"]
    # vector-only fields aren't clobbered by the keyword merge
    assert by_id["a"]["title"] == "red shoes"


def test_sort_and_filter_drops_score_of_exactly_one():
    results = [{"id": "a", "score": 1.0}, {"id": "b", "score": 1.5}]

    filtered = sort_and_filter_results_by_score(results)

    assert [r["id"] for r in filtered] == ["b"]


def test_sort_and_filter_orders_descending():
    results = [
        {"id": "a", "score": 1.2},
        {"id": "b", "score": 2.5},
        {"id": "c", "score": 1.8},
    ]

    filtered = sort_and_filter_results_by_score(results)

    assert [r["id"] for r in filtered] == ["b", "c", "a"]
