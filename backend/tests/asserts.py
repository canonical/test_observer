from httpx import Response


def assert_fails_validation(response: Response, field: str, type: str) -> None:
    assert response.status_code == 422
    problem = response.json()["detail"][0]
    assert problem["type"] == type
    assert problem["loc"][-1] == field
