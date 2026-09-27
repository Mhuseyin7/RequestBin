from app.services.codegen import curl

def test_curl_redacts_authorization():
    output = curl("POST", "https://example.com/hook", {"Authorization":"Bearer sensitive-token"}, "{}")
    assert "sensitive-token" not in output
    assert "••••" in output
