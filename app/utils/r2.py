"""Cloudflare R2 (S3-compatible) client helpers.

Locally the same code talks to the minio container from docker-compose.yml.
"""

from functools import lru_cache

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from app.core.config import settings


def is_configured() -> bool:
    """True when the R2 credentials are present. Callers with best-effort
    storage (e.g. verification document retention) check this to no-op
    gracefully instead of surfacing the 503 that _client() raises."""
    return bool(
        settings.R2_ENDPOINT_URL and settings.R2_ACCESS_KEY_ID and settings.R2_SECRET_ACCESS_KEY
    )


@lru_cache(maxsize=1)
def _client():
    if not is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Object storage is not configured",
        )
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name=settings.R2_REGION,
        config=Config(signature_version="s3v4"),
    )


def put_bytes(file_key: str, data: bytes, content_type: str, *, bucket: str | None = None) -> None:
    """Server-side direct upload of an in-memory object (no presign round-trip).

    Used where the backend itself holds the bytes — e.g. retaining verification
    documents. ``bucket`` overrides the default uploads bucket.
    """
    _client().put_object(
        Bucket=bucket or settings.R2_BUCKET,
        Key=file_key,
        Body=data,
        ContentType=content_type,
    )


def presign_put(file_key: str, content_type: str) -> str:
    """Presigned PUT URL; the client must send the same Content-Type header."""
    return _client().generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.R2_BUCKET,
            "Key": file_key,
            "ContentType": content_type,
        },
        ExpiresIn=settings.R2_PRESIGN_EXPIRE_SECONDS,
    )


def presign_get(file_key: str) -> str:
    """Presigned GET URL for reading a private object (e.g. rendering an avatar)."""
    return _client().generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.R2_BUCKET,
            "Key": file_key,
        },
        ExpiresIn=settings.R2_PRESIGN_EXPIRE_SECONDS,
    )


def delete_object(file_key: str) -> None:
    """Delete an object; deleting a nonexistent key is a no-op in S3/R2."""
    _client().delete_object(Bucket=settings.R2_BUCKET, Key=file_key)


def head_object(file_key: str) -> dict | None:
    """Object metadata ({size, content_type}) or None if the key does not exist."""
    try:
        resp = _client().head_object(Bucket=settings.R2_BUCKET, Key=file_key)
    except ClientError as exc:
        if exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
            return None
        raise
    return {
        "size": resp.get("ContentLength"),
        "content_type": resp.get("ContentType"),
    }
