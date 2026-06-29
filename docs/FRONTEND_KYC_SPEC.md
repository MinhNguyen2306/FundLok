# KYC (identity verification) — frontend integration spec

This describes the backend contract for **identity verification (KYC)**, powered by
[Didit](https://docs.didit.me). The user verifies their identity (ID document + liveness +
face match) on **Didit's hosted flow**; our backend creates the session, stores the
result, and is notified by a signed webhook.

The browser **never** touches the Didit API key. The frontend only talks to **our** API,
and opens a Didit-hosted `verification_url` that our backend returns.

All routes below (except the webhook, which is Didit→backend only) require
`Authorization: Bearer <access_token>` — the same auth used everywhere else.

---

## The flow (what the frontend does)

```
┌──────────┐  1. POST /kyc/start         ┌──────────┐
│ Frontend │ ──────────────────────────► │ Backend  │ ── creates Didit session
│ (browser)│ ◄────────────────────────── │ (FundLok)│
└──────────┘   { verification_url, ... }  └──────────┘
     │
     │ 2. open verification_url (redirect / new tab / iframe)
     ▼
┌──────────────────────────┐
│  Didit hosted flow        │  user scans ID + does liveness/face check
│  (verify.didit.me)        │
└──────────────────────────┘
     │ 3. Didit redirects user back to your callback page
     ▼
┌──────────┐  4. GET /kyc/status (poll)  ┌──────────┐
│ Frontend │ ──────────────────────────► │ Backend  │ ◄── 4b. Didit webhook
│          │ ◄────────────────────────── │          │     (source of truth)
└──────────┘   { status, is_approved }   └──────────┘
```

1. User clicks **"Verify my identity"** → frontend calls `POST /kyc/start`.
2. Frontend opens the returned `verification_url` (redirect, new tab, or iframe).
3. User finishes on Didit; Didit redirects them back to your callback page
   (default `${FRONTEND_URL}/kyc/callback`).
4. On the callback page (and/or wherever you show KYC state), poll `GET /kyc/status`
   until `is_terminal` is `true`. Meanwhile Didit calls our webhook, which is the
   **authoritative** source of the decision.

> **Important:** never treat "the user came back to the callback page" as proof of
> approval. The only authoritative result is `status` from `GET /kyc/status`, which the
> backend sets from Didit's signed webhook.

---

## Endpoints

### 1. `POST /kyc/start` — begin (or resume) verification

Creates a Didit session for the logged-in user and returns the hosted URL to open.
If the user already has an **unfinished** verification, the same session is returned
(no duplicate) — so it's safe to call this every time the user lands on the KYC screen.

- **Auth:** required.
- **Body:** optional. Send the user's locale so the Didit flow renders in their
  language:

  ```json
  { "language": "vi" }
  ```

  Accepts `vi`, `vi-VN`, `en`, `en_US`, etc. — it's normalized to ISO 639-1
  server-side. Omit it to use the backend default (`DIDIT_LANGUAGE`, currently
  Vietnamese). The language only applies when a **new** session is created;
  reused unfinished sessions keep their original language.
- **Response `201`:**

  ```json
  {
    "verification_id": "1f0e8c2a-...",
    "session_id": "4c5c7f3a-...",
    "status": "Not Started",
    "verification_url": "https://verify.didit.me/vi/session/3FaJ9wLqX2Mz"
  }
  ```

- **Errors:** `401` not authenticated · `502` `{ "detail": "..." }` if Didit is
  unreachable or misconfigured (API key / workflow id).

**Frontend:** open `verification_url`. Pick one presentation:

| Pattern | Code |
| --- | --- |
| Redirect (simplest, best for mobile) | `window.location.href = verification_url` |
| New tab | `window.open(verification_url, "_blank")` |
| Embedded iframe | `<iframe src={verification_url} allow="camera; microphone; fullscreen" />` |

---

### 2. `GET /kyc/status` — read the latest result

Returns the user's most recent verification. Poll this on the callback page.

- **Auth:** required.
- **Response `200`:**

  ```json
  {
    "verification_id": "1f0e8c2a-...",
    "session_id": "4c5c7f3a-...",
    "status": "Approved",
    "is_terminal": true,
    "is_approved": true,
    "verification_url": "https://verify.didit.me/session/3FaJ9wLqX2Mz",
    "updated_at": "2026-06-26T10:05:00Z"
  }
  ```

- **Errors:** `401` not authenticated · `404` `{ "detail": "No KYC verification found" }`
  if the user has never started KYC (treat as "not verified yet").

`is_terminal` → the verification is finished (stop polling). `is_approved` → identity
confirmed. See the status table below.

---

### 3. `POST /kyc/sync` — force-refresh from Didit (optional)

Pulls the latest decision directly from Didit and updates our DB, then returns the same
shape as `GET /kyc/status`. Use this as a **fallback** if the webhook is delayed and a
poll of `/kyc/status` still shows a non-terminal status after the user returns.

- **Auth:** required.
- **Body:** none.
- **Response `200`:** same shape as `GET /kyc/status`.
- **Errors:** `401` · `404` no verification · `502` Didit unreachable.

> Prefer `GET /kyc/status` for normal polling (cheap, reads our DB). Only call
> `/kyc/sync` occasionally — it hits Didit's API directly.

---

### 4. `POST /kyc/webhook` — Didit → backend (not called by the frontend)

Listed for completeness only. Didit calls this with an HMAC-signed payload; the backend
verifies the signature, dedupes, and updates the verification. **The frontend never
calls this.**

---

## Status values

`status` is one of Didit's exact, **case-sensitive** strings:

| `status` | `is_terminal` | `is_approved` | Suggested UI |
| --- | --- | --- | --- |
| `Not Started` | false | false | "Start verification" |
| `In Progress` | false | false | "Verification in progress…" (keep polling) |
| `Awaiting User` | false | false | "Waiting for you to finish" |
| `In Review` | false | false | "Under review — we'll notify you" (stop active polling) |
| `Approved` | true | true | ✅ "Identity verified" |
| `Declined` | true | false | ❌ "Verification failed" + retry CTA |
| `Resubmitted` | false | false | "Please redo some steps" (re-open `verification_url`) |
| `Abandoned` | true | false | "You didn't finish" + restart CTA |
| `Expired` | true | false | "Link expired" → call `/kyc/start` again |
| `Kyc Expired` | true | false | "Re-verification required" → `/kyc/start` again |

To restart after a terminal non-approved state, just call `POST /kyc/start` again — it
creates a fresh session.

---

## Suggested frontend implementation (React / TS)

```ts
const API = import.meta.env.VITE_API_URL; // your backend base URL

async function startKyc(token: string, locale: string) {
  const res = await fetch(`${API}/kyc/start`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ language: locale }), // e.g. "vi" or "vi-VN" from your i18n
  });
  if (!res.ok) throw new Error("Could not start verification");
  const { verification_url } = await res.json();
  window.location.href = verification_url; // open Didit's hosted flow
}

async function getKycStatus(token: string) {
  const res = await fetch(`${API}/kyc/status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 404) return { status: "Not Started", is_terminal: false, is_approved: false };
  return res.json();
}

// On the /kyc/callback page: poll until terminal.
async function pollUntilDone(token: string, onUpdate: (s: any) => void) {
  for (let i = 0; i < 20; i++) {              // ~1 min total
    const s = await getKycStatus(token);
    onUpdate(s);
    if (s.is_terminal) return s;
    await new Promise((r) => setTimeout(r, 3000));
  }
  // Still pending after polling — webhook may be delayed. Optional last resort:
  await fetch(`${API}/kyc/sync`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
  return getKycStatus(token);
}
```

### A "Verify Identity" button

```tsx
function VerifyIdentityButton({ token }: { token: string }) {
  return <button onClick={() => startKyc(token)}>Verify my identity</button>;
}
```

---

## Routing you need on the frontend

- A **callback page** at `/kyc/callback` (default; configurable via the backend's
  `DIDIT_CALLBACK_URL`). Didit redirects the user here after the flow. On mount, run
  `pollUntilDone(...)` and render the result based on the status table.
- Optionally a **KYC status screen** that calls `GET /kyc/status` on load to gate
  features behind `is_approved`.

---

## Notes & gotchas

- **Consent:** show a brief disclosure ("you'll be redirected to our verification
  partner Didit to scan your ID and take a selfie") **before** opening `verification_url`.
- **Camera permissions:** the Didit flow needs camera access. On iframe embeds, the
  `allow="camera; microphone; fullscreen"` attribute is required.
- **Mobile:** prefer full-page redirect over iframe — camera + liveness behave best.
- **No polling forever:** stop on `is_terminal`, or on `In Review` (a human will review;
  surface a "we'll email you" state and rely on a later refresh).
- **Auth only:** every call needs the user's `Authorization: Bearer` token; the user
  must be logged in before starting KYC.
```
