
CREATE TABLE users (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    email               TEXT          UNIQUE NOT NULL,
    phone               TEXT          UNIQUE,
    password_hash       TEXT,
    role                TEXT          NOT NULL 
        CHECK (role IN ('SME', 'INVESTOR', 'ADMIN')),
    status              TEXT          NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'PENDING_KYC', 'SUSPENDED', 'REJECTED')),
    created_at          TIMESTAMPTZ   DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   DEFAULT NOW()
);


CREATE TABLE projects (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name          TEXT          NOT NULL,
    tax_id              TEXT          UNIQUE,
    industry            TEXT,
    address             JSONB,
    incorporation_date  DATE,
    status              TEXT          NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('DRAFT', 'ACTIVE', 'ARCHIVED', 'SUSPENDED', 'CLOSED')),
    created_at          TIMESTAMPTZ   DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   DEFAULT NOW()
);

-- Project ownership (1 SME → many projects allowed in schema, 1 enforced in app)
CREATE TABLE project_ownerships (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        TEXT NOT NULL DEFAULT 'OWNER'
        CHECK (role IN ('OWNER', 'FINANCE', 'VIEWER', 'AUDITOR')),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (project_id, user_id)
);



-- Documents (KYC for users & projects, bank statements, invoices, etc.)
CREATE TABLE documents (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type         TEXT          NOT NULL 
        CHECK (entity_type IN ('USER', 'PROJECT')),
    entity_id           UUID          NOT NULL,          -- user.id or project.id
    purpose             TEXT          NOT NULL 
        CHECK (purpose IN ('KYC_ID', 'KYC_ADDRESS', 'KYC_BUSINESS_REG', 'BANK_STATEMENT', 'INVOICE', 'OTHER')),
    filename            TEXT          NOT NULL,
    mime_type           TEXT,
    status              TEXT          NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'UPLOADED', 'SCANNING', 'APPROVED', 'REJECTED', 'FAILED')),
    size_bytes          BIGINT,
    checksum_sha256     TEXT,
    storage_key         TEXT          NOT NULL,          -- S3 / R2 / equivalent key
    metadata            JSONB,
    verified_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ   DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   DEFAULT NOW()
);

CREATE INDEX idx_documents_entity     ON documents(entity_type, entity_id);
CREATE INDEX idx_documents_purpose     ON documents(purpose, status);

-- Loan applications
CREATE TABLE loan_applications (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID          NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    requested_amount    DECIMAL(15,2) NOT NULL CHECK (requested_amount > 0),
    purpose             TEXT,
    repayment_preference TEXT,
    status              TEXT          NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED')),
    submitted_at        TIMESTAMPTZ,
    decided_at          TIMESTAMPTZ,
    decision_note       TEXT,
    created_at          TIMESTAMPTZ   DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   DEFAULT NOW()
);

-- Documents attached to applications
CREATE TABLE application_documents (
    application_id      UUID          NOT NULL REFERENCES loan_applications(id) ON DELETE CASCADE,
    document_id         UUID          NOT NULL REFERENCES documents(id) ON DELETE RESTRICT,
    PRIMARY KEY (application_id, document_id)
);

-- Underwriting / scoring runs
CREATE TABLE score_runs (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id      UUID          NOT NULL REFERENCES loan_applications(id) ON DELETE CASCADE,
    status              TEXT          NOT NULL DEFAULT 'RUNNING'
        CHECK (status IN ('RUNNING', 'READY', 'LOCKED', 'FAILED')),
    overall_score       DECIMAL(5,2),
    risk_grade          TEXT,
    recommended_terms   JSONB,
    factor_results      JSONB,
    locked_at           TIMESTAMPTZ,
    created_at          TIMESTAMPTZ   DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   DEFAULT NOW()
);

-- Contracts
CREATE TABLE contracts (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id      UUID          REFERENCES loan_applications(id) ON DELETE SET NULL,
    score_run_id        UUID          REFERENCES score_runs(id) ON DELETE SET NULL,
    status              TEXT          NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'SIGNED', 'ACTIVE_PENDING_FUNDING', 'ACTIVE_FUNDED', 'CLOSED', 'DEFAULTED')),
    final_terms         JSONB         NOT NULL,
    signed_at           TIMESTAMPTZ,
    activated_at        TIMESTAMPTZ,
    target_amount       DECIMAL(15,2) NOT NULL CHECK (target_amount > 0),
    funded_amount       DECIMAL(15,2) NOT NULL DEFAULT 0 CHECK (funded_amount >= 0),
    created_at          TIMESTAMPTZ   DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   DEFAULT NOW()
);

-- Marketplace listings
CREATE TABLE listings (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id         UUID          UNIQUE NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    target_amount       DECIMAL(15,2) NOT NULL,
    min_ticket          DECIMAL(12,2) CHECK (min_ticket > 0),
    status              TEXT          NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'OPEN', 'FUNDED', 'CLOSED', 'CANCELLED')),
    funded_amount       DECIMAL(15,2) NOT NULL DEFAULT 0,
    open_at             TIMESTAMPTZ,
    close_at            TIMESTAMPTZ,
    created_at          TIMESTAMPTZ   DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   DEFAULT NOW()
);

-- Investor orders / commitments
CREATE TABLE orders (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id          UUID          NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    investor_id         UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount              DECIMAL(15,2) NOT NULL CHECK (amount > 0),
    status              TEXT          NOT NULL DEFAULT 'PENDING_PAYMENT'
        CHECK (status IN ('PENDING_PAYMENT', 'FILLED', 'CANCELLED', 'EXPIRED')),
    payment_confirmed_at TIMESTAMPTZ,
    created_at          TIMESTAMPTZ   DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   DEFAULT NOW()
);

-- Holdings (many-to-many bridge between investors and contracts)
CREATE TABLE holdings (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id         UUID          NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    investor_id         UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_id            UUID          REFERENCES orders(id) ON DELETE SET NULL,
    principal           DECIMAL(15,2) NOT NULL CHECK (principal > 0),
    share_ratio         DECIMAL(10,8) CHECK (share_ratio BETWEEN 0 AND 1),
    created_at          TIMESTAMPTZ   DEFAULT NOW(),
    UNIQUE (contract_id, investor_id)
);

-- Ledger (append-only financial trail)
CREATE TABLE ledger_entries (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id         UUID          NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    type                TEXT          NOT NULL 
        CHECK (type IN ('DISBURSEMENT', 'REPAYMENT', 'DISTRIBUTION', 'FEE', 'PENALTY')),
    amount              DECIMAL(15,2) NOT NULL,
    reference           TEXT,
    occurred_at         TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ   DEFAULT NOW(),
    created_by          UUID          REFERENCES users(id) ON DELETE SET NULL
);

-- Audit trail (very important)
CREATE TABLE audit_logs (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type         TEXT          NOT NULL,
    entity_id           UUID,
    action              TEXT          NOT NULL,
    actor_id            UUID          REFERENCES users(id) ON DELETE SET NULL,
    before_state        JSONB,
    after_state         JSONB,
    ip_address          INET,
    created_at          TIMESTAMPTZ   DEFAULT NOW()
);

-- =============================================================
-- Grant privileges to developer (should already have most via SUPERUSER)
-- =============================================================
-- Just in case you decide to remove SUPERUSER later:

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO edwardw;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO edwardw;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO edwardw;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO edwardw;

-- =============================================================
-- End of script v1.0 the genesis!
-- =============================================================

-- Idempotency keys (align with ORM / Alembic 0002–0003)
ALTER TABLE orders
  ADD COLUMN IF NOT EXISTS idempotency_key TEXT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_idempotency_key
  ON orders (idempotency_key);

ALTER TABLE ledger_entries
  ADD COLUMN IF NOT EXISTS idempotency_key TEXT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_ledger_entries_idempotency_key
  ON ledger_entries (idempotency_key);