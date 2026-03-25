

-- =============================================================
-- 2. Create dedicated development database
-- Edward needs to come up with complete, automated, best practice 
-- for managing anything DBA related, including db and account setup.
-- =============================================================

CREATE DATABASE fundlok
    OWNER edwardw
    ENCODING 'UTF8'
    LC_COLLATE 'en_US.utf8'
    LC_CTYPE 'en_US.utf8'
    TEMPLATE template0;

-- Optional: revoke public access (good habit)
REVOKE ALL ON DATABASE fundlok_dev FROM PUBLIC;
GRANT ALL PRIVILEGES ON DATABASE fundlok_dev TO edwardw;

