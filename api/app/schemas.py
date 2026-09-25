from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, HttpUrl
class RegisterIn(BaseModel): email: EmailStr; password: str = Field(min_length=12, max_length=256)
class LoginIn(BaseModel): email: EmailStr; password: str
class EndpointIn(BaseModel): name: str = Field(min_length=1, max_length=100); max_body_size: int = Field(default=1_048_576, ge=1024, le=10_485_760); expires_at: datetime | None = None
class ReplayIn(BaseModel): target_url: HttpUrl; method: str = Field(pattern="^(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)$"); headers: dict[str,str] = {}; body: str | None = None
