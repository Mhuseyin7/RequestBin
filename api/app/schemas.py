from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator
class RegisterIn(BaseModel): email: EmailStr; password: str = Field(min_length=12, max_length=256)
class LoginIn(BaseModel): email: EmailStr; password: str; totp_code: str | None = Field(default=None, pattern="^\\d{6}$")
class EndpointIn(BaseModel): name: str = Field(min_length=1, max_length=100); max_body_size: int = Field(default=1_048_576, ge=1024, le=10_485_760); expires_at: datetime | None = None
class ReplayIn(BaseModel): target_url: HttpUrl; method: str = Field(pattern="^(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)$"); headers: dict[str,str] = {}; body: str | None = None
class ApiKeyIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    scopes: list[str] = ["bins:read"]
    @field_validator("scopes")
    @classmethod
    def valid_scopes(cls, values: list[str]):
        allowed = {"bins:read", "bins:write", "requests:read", "requests:delete", "requests:replay"}
        unknown = set(values) - allowed
        if unknown: raise ValueError(f"Unsupported API key scope: {', '.join(sorted(unknown))}")
        return sorted(set(values))
class ForwardingRuleIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    target_url: HttpUrl
    enabled: bool = True
    condition: dict = {}
    transforms: list[dict] = []
    headers: dict[str, str] = {}
    timeout_seconds: int = Field(default=10, ge=1, le=30)
    retry_count: int = Field(default=2, ge=0, le=5)
class OrganizationIn(BaseModel): name: str = Field(min_length=1, max_length=120)
class MemberIn(BaseModel): email: EmailStr; role: str = Field(pattern="^(OWNER|ADMIN|DEVELOPER|VIEWER)$")
