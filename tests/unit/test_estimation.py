from app.ratelimit.estimation import TokenEstimator



def test_estimate_request_tokens() -> None:
    estimator = TokenEstimator(chars_per_token=4)
    payload = {"messages": [{"role": "user", "content": "abcdabcd"}]}
    assert estimator.estimate_request_tokens(payload) == 2


def test_resolve_actual_tokens_prefers_usage() -> None:
    estimator = TokenEstimator(chars_per_token=4)
    response = {"usage": {"total_tokens": 42}}
    assert estimator.resolve_actual_tokens(response, estimated=10) == 42
