import azure.functions as func

from app.functions.http import hello


def test_hello_returns_named_greeting() -> None:
    request = func.HttpRequest(
        method="GET",
        url="http://localhost/api/hello",
        params={"name": "Ada"},
        body=b"",
    )

    response = hello(request)

    assert response.status_code == 200
    assert response.get_body() == b"Hello, Ada!"
