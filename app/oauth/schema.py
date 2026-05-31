from enum import Enum

from pydantic import BaseModel, EmailStr, Field
from pydantic.alias_generators import to_camel
from pydantic import AliasChoices


class OAuthProvider(str, Enum):
	GOOGLE = "google"
	MICROSOFT = "microsoft"


class OAuthLoginRequest(BaseModel):
	provider: OAuthProvider
	token: str = Field(min_length=1, validation_alias=AliasChoices("access_token", "id_token"))

	model_config = {"alias_generator": to_camel, "populate_by_name": True}


class OAuthUserInfo(BaseModel):
	provider: OAuthProvider
	provider_subject: str
	email: EmailStr
	full_name: str | None = None
	email_verified: bool = False


class OAuthTokenResponse(BaseModel):
	access_token: str
	refresh_token: str
	token_type: str = "bearer"
