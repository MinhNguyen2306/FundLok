from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    GOOGLE_CLIENT_ID: str | None = None
    MICROSOFT_CLIENT_ID: str | None = None
    MICROSOFT_TENANT_ID: str = "common"
    MOCK_UPLOAD_BASE_URL: str = "https://mock-storage.fundlok.local/upload"
    FRONTEND_URL: str = "http://localhost:3000"
    CLOUDFLARE_TURNSTILE_SECRET_KEY: str | None = None

    # SMTP Configuration
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_SECURE: bool = False
    EMAILS_FROM_EMAIL: str = "noreply@fundlok.com"
    EMAILS_FROM_NAME: str = "FundLok"



settings = Settings()