# Loan application document upload — frontend integration spec

This describes the backend contract for the 5-step "Gửi hồ sơ vay" wizard, where an SME
borrower uploads documents for a loan application. Files go **directly from the browser to
Cloudflare R2** via presigned URLs — they are never POSTed to the API.

## Prerequisite: getting a loan_application_id

The wizard needs a `loan_application_id` before any upload. All routes below require
`Authorization: Bearer <access_token>` with the SME role.

- `POST /projects` — create the business, and optionally the loan application in the
  same request (the create form collects both). Body:

  ```json
  {
    "legal_name": "Công ty TNHH ABC",
    "tax_id": "0312345678",
    "industry": "manufacturing",
    "address": {"city": "HCMC"},
    "incorporation_date": "2019-05-20",
    "loan_application": {
      "requested_amount": "500000000",
      "purpose": "Mua máy móc",
      "repayment_preference": "monthly"
    }
  }
  ```

  Only `legal_name` is required; `loan_application` (and every field except its
  `requested_amount`) is optional. Response is the project plus a `loan_application`
  object (`null` if not sent) — `response.loan_application.id` is the
  `loan_application_id` used everywhere below.
- `GET /projects` — list the logged-in user's businesses.
- `POST /loans/applications` — alternative if the form is split: create the application
  separately (body: `{business_id: <project id>, requested_amount, purpose?, repayment_preference?}`) → returns `{id, project_id, status: "DRAFT", ...}`.
- `GET /projects/{project_id}/applications` — list that business's loan applications,
  newest first, **each including its `documents` array** (same shape as the confirm
  response below). Optional filter `?status=DRAFT` (case-insensitive; e.g. DRAFT,
  SUBMITTED). 403 if the project belongs to another user, 404 if it doesn't exist.
  Use this both to find an existing DRAFT to resume (instead of creating a duplicate)
  and to restore wizard state on load/refresh: a document with `status: "UPLOADED"`
  needs nothing — render its step as complete with `original_filename`.

Typical wizard boot:

```
const drafts = await GET /projects/{projectId}/applications?status=DRAFT
const app    = drafts[0] ?? await POST /loans/applications {business_id: projectId, ...}
// drafts[0].documents already tells you which steps are done
```

## Overall sequence

```
for each file the user selects (6 files total across the 5 wizard steps):
    1. POST /uploads/init-upload      -> { upload_url, file_key }   (one call PER FILE)
    2. PUT <upload_url> with the raw file bytes (browser -> R2 directly)
    3. keep file_key in wizard state

on the final "Gửi hồ sơ" click:
    4. POST /uploads/confirm with ALL collected file_keys (one batched call)
    5. then call the existing POST /loans/applications/{id}/submit
```

Recommended UX: run steps 1–2 immediately when the user drops a file into a wizard step
(with per-file progress), not all at once at the end. If you do batch, use
`Promise.allSettled` so one failed transfer can be retried individually.

## Wizard step → document_type mapping

| Wizard step | document_type | Allowed extensions | Max size |
|---|---|---|---|
| 1. Hồ sơ pháp lý — điều lệ công ty | `legal_charter` | .pdf | 25 MB |
| 1. Hồ sơ pháp lý — giấy ĐKKD | `business_registration` | .pdf | 25 MB |
| 2. Thuế GTGT (1 zip, 48 file thuế) | `vat_tax_zip` | .zip | 200 MB |
| 3. Báo cáo TC (B02-DN) | `financial_report` | .pdf | 25 MB |
| 4. Hóa đơn ĐT (12 tháng) | `e_invoice_data` | .zip .xlsx .csv .xml | 100 MB |
| 5. CIC | `cic_report` | .pdf | 25 MB |

Step 1 uploads **two** files (two init-upload calls); every other step uploads one.
Exactly one file per document_type per application.

Accepted content types per extension (the `content_type` you send must match the file's
extension, and the later PUT must use the exact same Content-Type header):

- `.pdf` → `application/pdf`
- `.zip` → `application/zip` or `application/x-zip-compressed`
- `.xlsx` → `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `.csv` → `text/csv`
- `.xml` → `application/xml` or `text/xml`

## Endpoint 1: initialize an upload (per file)

`POST /uploads/init-upload` — requires `Authorization: Bearer <access_token>` (SME role).
The loan application must exist, belong to the logged-in user, and still be in `DRAFT`.

Request body:

```json
{
  "loan_application_id": "e13f62bb-ee45-4d14-b0f1-e58c5838d4ff",
  "document_type": "legal_charter",
  "filename": "Điều lệ công ty.pdf",
  "content_type": "application/pdf",
  "size": 482133
}
```

`filename` is the user's original file name (display only — Vietnamese characters are fine).
`size` is `file.size` in bytes.

Response `201`:

```json
{
  "document_id": "14b3d46f-450a-4509-a007-320a271c504f",
  "file_key": "application_documents/{user_id}/{loan_application_id}/legal_charter.pdf",
  "upload_url": "https://<r2-endpoint>/...signed...",
  "expires_in": 900
}
```

- `upload_url` is valid for **15 minutes** and only for this one object — use it immediately.
- `file_key` is what you keep and later send to `/uploads/confirm`. Never construct it
  yourself; always use the returned value.
- Calling init-upload again for the same `document_type` is the official "replace file"
  flow: the backend reuses the same record and the new upload overwrites the old object.
  No delete call is needed.

## Step 2: upload the file to R2

```js
await fetch(upload_url, {
  method: "PUT",
  headers: { "Content-Type": file.type },  // MUST equal the content_type sent to init-upload
  body: file,
});
```

- No Authorization header here — the signature in the URL is the auth.
- A mismatched Content-Type makes R2 reject the request with 403.
- On failure (network drop etc.), simply redo init-upload + PUT for that one file.

## Endpoint 2: confirm uploads (per application, batched)

`POST /uploads/confirm` — same auth requirements as init-upload.

Request body:

```json
{
  "loan_application_id": "e13f62bb-ee45-4d14-b0f1-e58c5838d4ff",
  "file_keys": ["application_documents/.../legal_charter.pdf", "..."]
}
```

(1–20 keys; send all 6 collected keys at once.)

Response `200`:

```json
{
  "documents": [
    {
      "id": "...",
      "loan_application_id": "...",
      "document_type": "legal_charter",
      "file_key": "...",
      "original_filename": "Điều lệ công ty.pdf",
      "content_type": "application/pdf",
      "file_size_bytes": 482133,
      "status": "UPLOADED",
      "uploaded_at": "2026-06-11T08:52:25.270585Z"
    }
  ]
}
```

The backend HEAD-checks each object actually exists in R2 before flipping it to
`UPLOADED`. Confirm is idempotent — re-sending already-confirmed keys is a no-op.

## Errors to handle

All errors are FastAPI-style: `{ "detail": "<message>" }`.

| Status | When | Suggested UI |
|---|---|---|
| 400 | Invalid document_type / extension / content_type, file too large, application not in DRAFT, unknown file_key, object missing from storage on confirm | Show `detail` next to the offending file input |
| 401 | Missing/expired token | Refresh token / re-login flow |
| 403 | Application belongs to another user, or non-SME role | Generic "not authorized" |
| 404 | loan_application_id doesn't exist | Restart wizard |
| 503 | Object storage not configured (backend env issue) | "Thử lại sau" toast |
| PUT to R2 fails | Network drop, expired URL, Content-Type mismatch | Retry button → redo init-upload + PUT for that file |

The most useful 400 details to surface verbatim: extension/size messages, e.g.
`"Extension .pdf not allowed for vat_tax_zip (allowed: zip)"` and
`"Object not found in storage: <key>"` (means the PUT never completed — retry that file).

## Notes

- The R2 bucket needs a CORS rule allowing `PUT` from the frontend origin
  (localhost:3000 and the production domain) — without it the browser PUT fails preflight.
- Don't gzip/transform the file; send raw bytes.
- The 6 `file_key`s are stable per application (deterministic names), so persisting them
  in wizard state across page reloads is safe, but re-fetching via init-upload is also cheap.
