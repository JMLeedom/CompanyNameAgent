from company_name_agent.decision_policy import DecisionPolicy

def test_high_score_with_small_margin_requires_review():
    policy = DecisionPolicy()

    decision, _ = policy.classify_search(
        best_score=92.0,
        second_best_score=89.0,
    )

    assert decision == "POSSIBLE_MATCH"


def test_high_score_with_large_margin_is_match():
    policy = DecisionPolicy()

    decision, _ = policy.classify_search(
        best_score=92.0,
        second_best_score=70.0,
    )

    assert decision == "MATCH"