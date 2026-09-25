import pytest
from fastapi import HTTPException
from app.services.ssrf import validate_target
def test_localhost_is_blocked():
    with pytest.raises(HTTPException): validate_target("http://127.0.0.1/admin")
