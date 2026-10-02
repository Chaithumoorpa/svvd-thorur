import importlib
import os
import time

import pytest


@pytest.fixture(scope="module")
def lh():
    # The module pins the process to IST on import; restore the test process's
    # own timezone afterwards so date-sensitive tests elsewhere are unaffected.
    saved = os.environ.get("TZ")
    try:
        yield importlib.import_module("app.lambda_handler")
    finally:
        if saved is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = saved
        time.tzset()


def _http_event(path, method="GET", **extra):
    """Minimal API Gateway HTTP API (payload v2.0) event, as Lambda delivers it."""
    return {
        "version": "2.0",
        "routeKey": "$default",
        "rawPath": path,
        "rawQueryString": "",
        "headers": {"host": "api.example.org", "accept": "application/json"},
        "requestContext": {
            "http": {"method": method, "path": path, "protocol": "HTTP/1.1", "sourceIp": "203.0.113.9", "userAgent": "t"},
            "domainName": "api.example.org",
            "stage": "$default",
            "requestId": "r1",
        },
        "isBase64Encoded": False,
        **extra,
    }


def test_runs_in_ist(lh):
    assert time.timezone == -19800


def test_http_event_is_served_by_fastapi(lh):
    res = lh.handler(_http_event("/health"), None)
    assert res["statusCode"] == 200
    assert res["body"] == '{"status":"ok"}'


def test_task_dispatch(lh, monkeypatch):
    calls = []
    monkeypatch.setitem(lh.TASKS, "send_occasion_greetings", lambda: calls.append(1) or {"sent": 3})
    assert lh.handler({"task": "send_occasion_greetings"}, None) == {"task": "send_occasion_greetings", "ok": True, "sent": 3}
    assert calls == [1]


def test_unknown_task_is_an_error(lh):
    with pytest.raises(ValueError, match="Unknown task"):
        lh.handler({"task": "drop_everything"}, None)


def test_http_request_cannot_reach_the_task_path(lh, monkeypatch):
    """A field named "task" on an HTTP event (where a client controls the body,
    not the envelope) must still be routed to the web app, never to a job."""
    monkeypatch.setitem(lh.TASKS, "migrate", lambda: pytest.fail("task ran from an HTTP event"))
    res = lh.handler(_http_event("/health", task="migrate"), None)
    assert res["statusCode"] == 200


def test_cli_jobs_are_registered(lh):
    assert set(lh.TASKS) == {"migrate", "send_occasion_greetings", "generate_festival_announcements"}
