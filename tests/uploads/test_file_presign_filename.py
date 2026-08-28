"""A client filename must never reach an object key or a URL unsanitised.

Found by an input-validation sweep. `POST /files/presign` built its key as
`fundlok/{business_id}/{uuid4}/{filename}` from an unbounded, unvalidated client
string, then interpolated that key into the upload URL's `?key=` parameter
without encoding it. The sibling loan-application flow derives its key entirely
server-side; this one now sanitises.

The sanitiser is unit-tested directly as well as through the endpoint, because
it is the piece that has to hold when real R2 presigning replaces the mock URL.
"""

import pytest
from sqlalchemy import select

from app.lending.models import Document
from app.uploads.schemas import safe_object_filename


class TestSafeObjectFilename:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            # Traversal segments. S3/R2 keys are opaque so this is not
            # filesystem traversal, but an HTTP client that normalises ".." in
            # the URL path signs one key and writes another.
            ("../../../etc/passwd", "passwd"),
            # "%" collapses to "_", then the leading dots are stripped.
            ("..%2F..%2Fevil.pdf", "_2F.._2Fevil.pdf"),
            ("subdir/report.pdf", "report.pdf"),
            # Windows separators — a Windows client sends the full local path.
            (r"C:\Users\me\report.pdf", "report.pdf"),
            # URL metacharacters would split or truncate the ?key= parameter.
            ("in&voice?x=1#frag.pdf", "in_voice_x_1_frag.pdf"),
            ("my report.pdf", "my_report.pdf"),
            # Control characters have no business in a key that may be logged
            # or echoed into a header.
            # A RUN of unsafe characters collapses to one "_", so "\r\n" and
            # ": " each become a single underscore.
            ("evil\r\nX-Injected: 1.pdf", "evil_X-Injected_1.pdf"),
            ("tab\there.pdf", "tab_here.pdf"),
            # Nothing usable left: the uuid4 segment carries identity anyway.
            ("..", "upload"),
            ("/", "upload"),
            ("...", "upload"),
            # Leading dots stripped so a key segment cannot be a dotfile.
            (".htaccess", "htaccess"),
            # Ordinary names pass through untouched.
            ("Q3-report_final.pdf", "Q3-report_final.pdf"),
        ],
    )
    def test_sanitises(self, raw, expected):
        assert safe_object_filename(raw) == expected

    def test_bounds_the_key_segment(self):
        # The schema caps input at 255, but the helper is callable directly and
        # must not depend on that.
        assert len(safe_object_filename("a" * 5000 + ".pdf")) == 255

    def test_never_returns_empty(self):
        for raw in ("", "   ", "///", "..", "\x00"):
            assert safe_object_filename(raw)


async def _presign(client, sme, project_id, filename):
    return await client.post(
        "/files/presign",
        json={
            "business_id": project_id,
            "purpose": "INVOICE",
            "filename": filename,
            "mime_type": "application/pdf",
        },
        headers=sme["headers"],
    )


async def test_traversal_filename_cannot_escape_the_project_prefix(
    client, make_user, make_project, db_session
):
    sme = await make_user(role="SME")
    project = await make_project(sme)

    resp = await _presign(client, sme, project["id"], "../../../other-tenant/steal.pdf")
    assert resp.status_code == 201, resp.text

    doc = (
        await db_session.execute(
            select(Document).where(Document.id == resp.json()["file_id"])
        )
    ).scalar_one()

    assert doc.storage_key.startswith(f"fundlok/{project['id']}/")
    assert ".." not in doc.storage_key
    assert doc.storage_key.endswith("/steal.pdf")


async def test_the_users_own_filename_is_still_stored_for_display(
    client, make_user, make_project, db_session
):
    # Sanitising is about what reaches the KEY. Mangling what the UI shows the
    # user would be a worse product for no security gain.
    sme = await make_user(role="SME")
    project = await make_project(sme)
    original = "Báo cáo tài chính 2026.pdf"

    resp = await _presign(client, sme, project["id"], original)
    assert resp.status_code == 201, resp.text

    doc = (
        await db_session.execute(
            select(Document).where(Document.id == resp.json()["file_id"])
        )
    ).scalar_one()

    assert doc.filename == original
    # ...while the key itself carries no spaces or non-ASCII.
    assert " " not in doc.storage_key
    assert doc.storage_key.isascii()


async def test_upload_url_encodes_the_key(client, make_user, make_project):
    sme = await make_user(role="SME")
    project = await make_project(sme)

    resp = await _presign(client, sme, project["id"], "report.pdf")
    assert resp.status_code == 201, resp.text

    upload_url = resp.json()["upload_url"]
    key = upload_url.split("?key=", 1)[1]
    # A path-shaped value in a query parameter: unencoded "/" would let the key
    # be read as part of the path, and "&" would truncate it.
    assert "/" not in key
    assert "&" not in key
    assert "%2F" in key


@pytest.mark.parametrize("filename", ["", "a" * 256])
async def test_filename_length_is_bounded(client, make_user, make_project, filename):
    sme = await make_user(role="SME")
    project = await make_project(sme)

    resp = await _presign(client, sme, project["id"], filename)

    assert resp.status_code == 422, resp.text
