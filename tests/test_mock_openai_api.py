import scripts.mock_openai_api as mock_openai_api


def test_route_request_supports_v1_prefix(monkeypatch) -> None:
    monkeypatch.setattr(mock_openai_api, "API_PREFIX", "/v1")

    status, payload = mock_openai_api._route_request("GET", "/v1/models")

    assert status == 200
    assert payload["data"][0]["id"]

    status, payload = mock_openai_api._route_request(
        "POST",
        "/v1/chat/completions",
        {
            "model": "demo-model",
            "messages": [{"role": "user", "content": "Context:\n- Water.\n\nQuestion:\nReady?"}],
        },
    )

    assert status == 200
    assert payload["model"] == "demo-model"
    assert payload["choices"][0]["message"]["content"].startswith("SHORT:")


def test_route_request_supports_v3_prefix(monkeypatch) -> None:
    monkeypatch.setattr(mock_openai_api, "API_PREFIX", "/v3")

    status, payload = mock_openai_api._route_request("GET", "/v3/models")

    assert status == 200
    assert payload["data"][0]["id"]

    status, payload = mock_openai_api._route_request(
        "POST",
        "/v3/chat/completions",
        {
            "model": "demo-model",
            "messages": [{"role": "user", "content": "Context:\n- Water.\n\nQuestion:\nReady?"}],
        },
    )

    assert status == 200
    assert payload["model"] == "demo-model"
    assert payload["choices"][0]["message"]["content"].startswith("SHORT:")
