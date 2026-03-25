-- =====================================================================
-- COMPLETE SAFE RE-SEED SCRIPT for fundlok_dev (MVP Test Data - March 2026)
-- Fully idempotent: TRUNCATE first + ON CONFLICT DO NOTHING everywhere
-- Valid UUIDs only — no syntax errors
-- Paste and run the WHOLE block at once
-- =====================================================================

-- 0. Safe cleanup — reverse dependency order to avoid FK constraint violations
DO $$
BEGIN
    TRUNCATE TABLE audit_logs           CASCADE;
    TRUNCATE TABLE ledger_entries       CASCADE;
    TRUNCATE TABLE holdings             CASCADE;
    TRUNCATE TABLE orders               CASCADE;
    TRUNCATE TABLE listings             CASCADE;
    TRUNCATE TABLE contracts            CASCADE;
    TRUNCATE TABLE score_runs           CASCADE;
    TRUNCATE TABLE application_documents CASCADE;
    TRUNCATE TABLE loan_applications    CASCADE;
    TRUNCATE TABLE documents            CASCADE;
    TRUNCATE TABLE project_ownerships   CASCADE;
    TRUNCATE TABLE projects             CASCADE;
    TRUNCATE TABLE users                CASCADE;
END $$;

-- =====================================================================
-- 1. Users (4 total: 1 SME, 2 Investors, 1 Admin)
INSERT INTO users (id, email, phone, password_hash, role, status, created_at, updated_at) VALUES
('00000000-0000-0000-0000-000000000001', 'sme.owner@example.vn', '+84912345678', '$2b$12$abcdefghijklmnopqrstuvwx.yz0123456789ABCDEFGHIJK', 'SME',     'ACTIVE', '2026-02-15 09:30:00+07', NOW()),
('00000000-0000-0000-0000-000000000002', 'investor1@example.com', '+6587654321', '$2b$12$abcdefghijklmnopqrstuvwx.yz0123456789ABCDEFGHIJK', 'INVESTOR', 'ACTIVE', '2026-02-10 14:45:00+07', NOW()),
('00000000-0000-0000-0000-000000000003', 'investor2@example.com', NULL,          '$2b$12$abcdefghijklmnopqrstuvwx.yz0123456789ABCDEFGHIJK', 'INVESTOR', 'PENDING_KYC', '2026-02-20 10:15:00+07', NOW()),
('00000000-0000-0000-0000-000000000004', 'admin@fundlok.vn',     '+84987654321', '$2b$12$abcdefghijklmnopqrstuvwx.yz0123456789ABCDEFGHIJK', 'ADMIN',    'ACTIVE', '2026-01-05 08:00:00+07', NOW())
ON CONFLICT (id) DO NOTHING;

-- Cleartext passwords for your Excel sheet (never store in DB!):
-- sme.owner@example.vn     → test123
-- investor1@example.com    → investor456
-- investor2@example.com    → secure789
-- admin@fundlok.vn         → admin2026!

-- =====================================================================
-- 2. Projects (2 - both linked to SME, one ACTIVE, one ARCHIVED)
INSERT INTO projects (id, legal_name, tax_id, industry, address, incorporation_date, status, created_at, updated_at) VALUES
('10000000-0000-0000-0000-000000000001', 'Công ty TNHH ABC Việt Nam', '0101234567', 'Retail', '{"street": "123 Lê Lợi", "city": "HCM", "country": "Vietnam"}', '2024-05-10', 'ACTIVE',   '2026-02-16 10:00:00+07', NOW()),
('10000000-0000-0000-0000-000000000002', 'Dự án XYZ Coffee Roastery', '0109876543', 'Food & Beverage', '{"street": "45 Nguyễn Huệ", "city": "Đà Nẵng", "country": "Vietnam"}', '2025-01-15', 'ARCHIVED', '2026-01-20 15:30:00+07', NOW())
ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- 3. Project Ownerships (SME owns both, extra VIEWER example)
INSERT INTO project_ownerships (id, project_id, user_id, role, created_at) VALUES
('20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'OWNER',  '2026-02-16 10:05:00+07'),
('20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'OWNER',  '2026-01-20 15:35:00+07'),
('20000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 'VIEWER', '2026-02-18 11:20:00+07')
ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- 4. Documents (6 - mix of KYC and cashflow)
INSERT INTO documents (id, entity_type, entity_id, purpose, filename, mime_type, status, size_bytes, checksum_sha256, storage_key, metadata, verified_at, created_at) VALUES
('30000000-0000-0000-0000-000000000001', 'USER',    '00000000-0000-0000-0000-000000000001', 'KYC_ID', 'cmnd_sme.jpg', 'image/jpeg', 'APPROVED', 1240000, 'abc123checksum...', 'kyc/sme/cmnd.jpg', '{"confidence": 0.98}', '2026-02-17 09:00:00+07', '2026-02-16 11:00:00+07'),
('30000000-0000-0000-0000-000000000002', 'USER',    '00000000-0000-0000-0000-000000000002', 'KYC_ADDRESS', 'utility_bill.pdf', 'application/pdf', 'APPROVED', 850000, 'def456...', 'kyc/inv1/bill.pdf', NULL, '2026-02-19 14:30:00+07', '2026-02-18 13:00:00+07'),
('30000000-0000-0000-0000-000000000003', 'PROJECT', '10000000-0000-0000-0000-000000000001', 'BANK_STATEMENT', 'bank_2025_12.pdf', 'application/pdf', 'APPROVED', 3200000, 'ghi789...', 'projects/a1/statements/dec25.pdf', '{"months_covered": ["2025-10", "2025-11", "2025-12"]}', NULL, '2026-02-20 10:45:00+07'),
('30000000-0000-0000-0000-000000000004', 'PROJECT', '10000000-0000-0000-0000-000000000001', 'INVOICE', 'invoice_001.pdf', 'application/pdf', 'SCANNING', 450000, NULL, 'projects/a1/invoices/inv001.pdf', NULL, NULL, '2026-03-01 08:15:00+07'),
('30000000-0000-0000-0000-000000000005', 'USER',    '00000000-0000-0000-0000-000000000003', 'KYC_ID', 'passport_inv2.jpg', 'image/jpeg', 'PENDING', 980000, NULL, 'kyc/inv2/passport.jpg', NULL, NULL, '2026-02-25 16:00:00+07'),
('30000000-0000-0000-0000-000000000006', 'PROJECT', '10000000-0000-0000-0000-000000000002', 'BANK_STATEMENT', 'old_bank.pdf', 'application/pdf', 'APPROVED', 2100000, 'jkl012...', 'projects/b2/old_statements.pdf', NULL, '2026-01-25 11:00:00+07', '2026-01-20 16:00:00+07')
ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- 5. Loan Applications (2 - one DRAFT, one SUBMITTED)
INSERT INTO loan_applications (id, project_id, requested_amount, purpose, repayment_preference, status, submitted_at, created_at) VALUES
('40000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 500000000, 'Mở rộng cửa hàng bán lẻ', 'Revenue share 8%', 'SUBMITTED', '2026-02-22 09:30:00+07', '2026-02-20 08:00:00+07'),
('40000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', 1200000000, 'Mua thêm thiết bị pha chế', 'Fixed monthly', 'DRAFT', NULL, '2026-03-04 14:00:00+07')
ON CONFLICT (id) DO NOTHING;

-- Link documents to applications
INSERT INTO application_documents (application_id, document_id) VALUES
('40000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000001'),
('40000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000003'),
('40000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000004'),
('40000000-0000-0000-0000-000000000002', '30000000-0000-0000-0000-000000000001')
ON CONFLICT (application_id, document_id) DO NOTHING;

-- =====================================================================
-- 6. Score Run (1 for the submitted application)
INSERT INTO score_runs (id, application_id, status, overall_score, risk_grade, recommended_terms, factor_results, created_at) VALUES
('50000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', 'READY', 72.5, 'B+', '{"interest_rate": 0.18, "tenure_months": 18, "revenue_share_pct": 8.5}', '{"cashflow_quality": 85, "industry_risk": 60}', '2026-02-23 11:15:00+07')
ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- 7. Contract (1 - signed)
INSERT INTO contracts (id, application_id, score_run_id, status, final_terms, signed_at, target_amount, funded_amount, created_at) VALUES
('60000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', 'SIGNED', '{"revenue_share_pct": 8.5, "cap_multiple": 1.8}', '2026-02-25 13:45:00+07', 500000000, 0, '2026-02-24 10:00:00+07')
ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- 8. Listing (1 - open)
INSERT INTO listings (id, contract_id, target_amount, min_ticket, status, open_at, close_at, funded_amount, created_at) VALUES
('70000000-0000-0000-0000-000000000001', '60000000-0000-0000-0000-000000000001', 500000000, 10000000, 'OPEN', '2026-02-26 09:00:00+07', '2026-03-10 23:59:00+07', 0, '2026-02-25 15:30:00+07')
ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- 9. Orders (4 - from both investors)
INSERT INTO orders (id, listing_id, investor_id, amount, status, payment_confirmed_at, created_at) VALUES
('80000000-0000-0000-0000-000000000001', '70000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 150000000, 'FILLED', '2026-02-27 10:20:00+07', '2026-02-26 14:00:00+07'),
('80000000-0000-0000-0000-000000000002', '70000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 80000000,  'FILLED', '2026-02-28 11:05:00+07', '2026-02-27 09:30:00+07'),
('80000000-0000-0000-0000-000000000003', '70000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000003', 50000000,  'PENDING_PAYMENT', NULL, '2026-03-01 16:45:00+07'),
('80000000-0000-0000-0000-000000000004', '70000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 120000000, 'FILLED', '2026-03-03 12:10:00+07', '2026-03-02 08:00:00+07')
ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- 10. Holdings (3 - after confirmation)
INSERT INTO holdings (id, contract_id, investor_id, order_id, principal, share_ratio, created_at) VALUES
('90000000-0000-0000-0000-000000000001', '60000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', '80000000-0000-0000-0000-000000000001', 150000000, 0.3000, '2026-02-27 10:25:00+07'),
('90000000-0000-0000-0000-000000000002', '60000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', '80000000-0000-0000-0000-000000000002', 80000000,  0.1600, '2026-02-28 11:10:00+07'),
('90000000-0000-0000-0000-000000000003', '60000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', '80000000-0000-0000-0000-000000000004', 120000000, 0.2400, '2026-03-03 12:15:00+07')
ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- 11. Ledger Entries (5 - disbursement + repayments + distributions)
INSERT INTO ledger_entries (id, contract_id, type, amount, reference, occurred_at, created_at, created_by) VALUES
('a0000000-0000-0000-0000-000000000001', '60000000-0000-0000-0000-000000000001', 'DISBURSEMENT', 500000000, 'Bank transfer to SME', '2026-03-04 09:00:00+07', '2026-03-04 09:05:00+07', '00000000-0000-0000-0000-000000000004'),
('a0000000-0000-0000-0000-000000000002', '60000000-0000-0000-0000-000000000001', 'REPAYMENT',  25000000, 'Daily revenue share - Mar 5', '2026-03-05 23:59:00+07', NOW(), NULL),
('a0000000-0000-0000-0000-000000000003', '60000000-0000-0000-0000-000000000001', 'DISTRIBUTION', 7500000, 'Pro-rata to investors (30%)', '2026-03-06 00:05:00+07', NOW(), NULL),
('a0000000-0000-0000-0000-000000000004', '60000000-0000-0000-0000-000000000001', 'DISTRIBUTION', 4000000, 'Pro-rata (16%)', '2026-03-06 00:05:00+07', NOW(), NULL),
('a0000000-0000-0000-0000-000000000005', '60000000-0000-0000-0000-000000000001', 'DISTRIBUTION', 6000000, 'Pro-rata (24%)', '2026-03-06 00:05:00+07', NOW(), NULL)
ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- 12. Audit Logs (3 examples)
INSERT INTO audit_logs (id, entity_type, entity_id, action, actor_id, before_state, after_state, created_at) VALUES
('b0000000-0000-0000-0000-000000000001', 'loan_application', '40000000-0000-0000-0000-000000000001', 'SUBMIT', '00000000-0000-0000-0000-000000000001', NULL, '{"status": "SUBMITTED"}', '2026-02-22 09:30:00+07'),
('b0000000-0000-0000-0000-000000000002', 'contract', '60000000-0000-0000-0000-000000000001', 'SIGN', '00000000-0000-0000-0000-000000000001', '{"status": "DRAFT"}', '{"status": "SIGNED"}', '2026-02-25 13:45:00+07'),
('b0000000-0000-0000-0000-000000000003', 'order', '80000000-0000-0000-0000-000000000001', 'CONFIRM_PAYMENT', '00000000-0000-0000-0000-000000000004', '{"status": "PENDING_PAYMENT"}', '{"status": "FILLED"}', '2026-02-27 10:20:00+07')
ON CONFLICT (id) DO NOTHING;

-- =====================================================================
-- Done!
-- Quick verification queries (run these after):
-- SELECT COUNT(*) FROM users;                -- should be 4
-- SELECT COUNT(*) FROM project_ownerships;   -- should be 3
-- SELECT COUNT(*) FROM documents;            -- should be 6
-- SELECT COUNT(*) FROM holdings;             -- should be 3
-- SELECT COUNT(*) FROM loan_applications;    -- should be 2