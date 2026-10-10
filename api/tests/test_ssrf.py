import pytest
from fastapi import HTTPException
from app.services.ssrf import validate_target
def test_localhost_is_blocked():
    with pytest.raises(HTTPException): validate_target("http://127.0.0.1/admin")
def test_embedded_credentials_are_blocked():
    with pytest.raises(HTTPException): validate_target("https://user:password@example.com/webhook")
