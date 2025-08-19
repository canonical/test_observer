from fastapi.testclient import TestClient


def test_saml_login_redirects_to_idp(test_client: TestClient):
    response = test_client.get("/v1/auth/saml/login", follow_redirects=False)

    assert response.status_code == 307
    assert "location" in response.headers
    assert "SSOService.php" in response.headers["location"]
