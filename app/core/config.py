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
    FRONTEND_URL: str = "https://www.fundlok.com"
    ALLOWED_ORIGINS: str = "https://www.fundlok.com,https://fundlok.com,https://fundlok-front-end.vercel.app,http://localhost:3000,http://127.0.0.1:3000"
    CLOUDFLARE_TURNSTILE_SECRET_KEY: str | None = None

    # Encrypts users.totp_secret at rest (app/auth/totp_crypto.py). A SEPARATE
    # secret from SECRET_KEY on purpose: sharing them would mean rotating the
    # JWT key locks every 2FA user out of their authenticator. Unset means
    # enrolment is refused — the feature fails closed rather than storing
    # password-equivalent secrets in plaintext.
    TOTP_ENCRYPTION_KEY: str | None = None

    # Cloudflare R2 (S3-compatible). Locally, point at the minio container.
    R2_ENDPOINT_URL: str | None = None
    R2_ACCESS_KEY_ID: str | None = None
    R2_SECRET_ACCESS_KEY: str | None = None
    R2_BUCKET: str = "fundlok-uploads"
    # Bucket for retained KYC/KYB verification documents (falls back to
    # R2_BUCKET when unset; keys are prefixed verification/KYC|KYB/<id>/).
    R2_VERIFICATION_BUCKET: str | None = None
    R2_REGION: str = "auto"
    R2_PRESIGN_EXPIRE_SECONDS: int = 15 * 60

    # SMTP Configuration
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_SECURE: bool = False
    EMAILS_FROM_EMAIL: str = "noreply@fundlok.com"
    EMAILS_FROM_NAME: str = "FundLok"

    # Didit KYC / identity verification (https://docs.didit.me)
    # The verification API authenticates with a static secret on x-api-key.
    DIDIT_API_KEY: str | None = None
    DIDIT_WORKFLOW_ID: str | None = None  # KYC workflow UUID (investors), passed per session
    DIDIT_KYB_WORKFLOW_ID: str | None = None  # KYB workflow UUID (SMEs / business verification)
    # Webhook destination secret_shared_key (X-Signature-V2 HMAC). Accepts the
    # legacy DIDIT_WEBHOOK_SECRET_KEY name as a fallback alias.
    DIDIT_WEBHOOK_SECRET: str | None = None
    DIDIT_WEBHOOK_SECRET_KEY: str | None = None
    DIDIT_BASE_URL: str = "https://verification.didit.me"
    DIDIT_CALLBACK_URL: str | None = None  # FE return URL; defaults to FRONTEND_URL/kyc/callback
    DIDIT_LANGUAGE: str = "vi"  # ISO 639-1 UI language for the hosted flow (Vietnamese)

    # GVerify / GHub eKYC (Datatrust, API v2.5.1) — direct-API KYC provider,
    # parallel to Didit. See docs/specs/gverify/ekyc-kyc-verification.md.
    GVERIFY_BASE_URL: str | None = None  # partner-provided {api-base-url}
    GVERIFY_API_KEY: str | None = None  # x-api-key header value
    GVERIFY_PARTNER_CODE: str | None = None  # partner/subpartner "code" sent per request
    GVERIFY_OS_TYPE: str = "fundlok-backend"  # os-type header
    GVERIFY_MIN_OCR_CONFIDENCE: float = 0.85  # min person_number/full_name confidence
    # KYB (business verification) — docs/specs/gverify/ekyb-kyb-verification.md
    GVERIFY_MIN_KYB_OCR_CONFIDENCE: float = 0.85  # min name/tax_code confidence
    # Require the SME's KYC-verified person_number to appear among the
    # certificate's legal representatives (spec Rule 7, default off pending review).
    GVERIFY_KYB_REQUIRE_REP_MATCH: bool = False

    @property
    def cors_origins(self) -> list[str]:
        origins = [o.strip().rstrip("/") for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
        frontend = self.FRONTEND_URL.strip().rstrip("/") if self.FRONTEND_URL else None
        if frontend and frontend not in origins:
            origins.append(frontend)
        return origins



settings = Settings()