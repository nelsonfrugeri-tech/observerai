import json
from unittest.mock import patch

import pytest
from google import genai

from observerai.context import TraceContext
from observerai.gemini import metric_generate_content


@pytest.fixture(autouse=True)
def set_context():
    TraceContext.set_trace_id("trace")
    TraceContext.set_span_id("span")
    TraceContext.set_flow_id("flow")
    yield


def build_response():
    return genai.types.GenerateContentResponse(
        candidates=[
            genai.types.Candidate(
                content=genai.types.Content(parts=[genai.types.Part(text="Pong")])
            )
        ],
        usage_metadata=genai.types.GenerateContentResponseUsageMetadata(
            prompt_token_count=1,
            candidates_token_count=2,
            total_token_count=3,
        ),
    )


def test_metric_generate_content_success(capsys):
    client = genai.Client(api_key="dummy")

    with patch.object(
        genai.models.Models, "generate_content", return_value=build_response()
    ):

        @metric_generate_content(metadata={"user_id": 42})
        def call():
            return client.models.generate_content(
                model="gemini-2.0-pro",
                contents=["Ping"],
                config=genai.types.GenerateContentConfig(temperature=0.2),
            )

        resp = call()
        assert resp.text == "Pong"

    out = capsys.readouterr().out.strip().splitlines()[-1]
    data = json.loads(out)
    assert data["name"] == "gemini-2.0-pro"
    assert data["provider"] == "gemini"
    assert data["endpoint"] == "/generate_content"
    assert data["token_usage"] == {"prompt": 1, "completion": 2, "total": 3}
    assert data["conversation"]["question"]["content"] == "Ping"
    assert data["conversation"]["answer"]["content"] == "Pong"
    assert data["metadata"] == {"user_id": 42}


def test_metric_generate_content_error(capsys):
    client = genai.Client(api_key="dummy")

    def raise_error(*args, **kwargs):
        raise genai.errors.APIError(500, {"message": "Internal Error"})

    with patch.object(genai.models.Models, "generate_content", side_effect=raise_error):

        @metric_generate_content(metadata={"user_id": 42})
        def call():
            return client.models.generate_content(
                model="gemini-2.0-pro",
                contents=["Ping"],
                config=genai.types.GenerateContentConfig(temperature=0.2),
            )

        resp = call()
        assert resp is None

    captured = capsys.readouterr()
    out_line = captured.out.strip().splitlines()[-1]
    data = json.loads(out_line)
    assert data["response"]["status_code"] == 500
    assert "exception" in data
    assert data["conversation"]["answer"] is None
    assert "Internal Error" in data["exception"]["message"]
    assert captured.err != ""
