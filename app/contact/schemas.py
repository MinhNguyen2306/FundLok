from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class ContactPurpose(str, Enum):
    """What the sender is writing about, chosen from the form's dropdown.

    The values are the contract with the frontend
    (`lib/constants/contact-purposes.ts`) — they are stored and matched on, so
    renaming one breaks submissions from any browser still running the old
    bundle. `label` is the English text used in the notification subject; it is
    deliberately server-side so the mail header never carries client-supplied
    text.
    """

    PARTNERSHIP = "partnership"
    SME_FUNDING = "sme_funding"
    INVESTING = "investing"
    SUPPORT = "support"
    MEDIA = "media"
    OTHER = "other"

    @property
    def label(self) -> str:
        return _PURPOSE_LABELS[self]


_PURPOSE_LABELS: dict[ContactPurpose, str] = {
    ContactPurpose.PARTNERSHIP: "Partnership",
    ContactPurpose.SME_FUNDING: "SME funding",
    ContactPurpose.INVESTING: "Investing",
    ContactPurpose.SUPPORT: "Support",
    ContactPurpose.MEDIA: "Media",
    ContactPurpose.OTHER: "Other",
}


class ContactRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    # Optional so a browser running a cached pre-dropdown bundle still submits
    # successfully; those land under the "General" prefix.
    purpose: ContactPurpose | None = None
    # The form has always sent a subject; it used to be dropped silently here.
    subject: str | None = Field(default=None, max_length=300)
    message: str = Field(min_length=1, max_length=5000)
    turnstile_token: str | None = None
