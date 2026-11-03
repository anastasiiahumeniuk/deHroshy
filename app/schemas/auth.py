from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.validation import (
    normalize_email,
    validate_password_strength,
)


class EmailRequest(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: object) -> object:
        return normalize_email(value)


class RegisterRequest(EmailRequest):
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)


class LoginRequest(EmailRequest):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
