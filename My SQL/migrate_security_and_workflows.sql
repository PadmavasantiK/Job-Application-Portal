-- Legacy MySQL migration from the earlier backend; do not run for the SQLite app.
USE JobApplicationPortal;

-- Review duplicate applications first; remove/merge duplicates before adding the unique key.
-- SELECT user_id, job_id, COUNT(*) FROM Application GROUP BY user_id, job_id HAVING COUNT(*) > 1;

ALTER TABLE Admin
    ADD COLUMN password_hash VARCHAR(255) NULL,
    ADD COLUMN role ENUM('admin') NOT NULL DEFAULT 'admin';

ALTER TABLE Job
    MODIFY employer_id INT NOT NULL,
    ADD CONSTRAINT chk_job_salary CHECK (salary IS NULL OR salary >= 0),
    ADD CONSTRAINT chk_job_age CHECK (age IS NULL OR age >= 0),
    ADD INDEX idx_job_employer (employer_id),
    ADD INDEX idx_job_posted_date (posted_date);

ALTER TABLE JobSeeker
    MODIFY first_name VARCHAR(50) NOT NULL,
    MODIFY last_name VARCHAR(50) NOT NULL,
    MODIFY email VARCHAR(100) NOT NULL,
    MODIFY skills VARCHAR(255) NOT NULL;

UPDATE Application SET status = 'Pending'
WHERE status IS NULL OR status NOT IN ('Pending','Shortlisted','Interview','Selected','Rejected');
ALTER TABLE Application
    MODIFY application_id INT NOT NULL AUTO_INCREMENT,
    MODIFY status ENUM('Pending','Shortlisted','Interview','Selected','Rejected') NOT NULL DEFAULT 'Pending',
    MODIFY user_id INT NOT NULL,
    MODIFY job_id INT NOT NULL,
    ADD CONSTRAINT uq_application_user_job UNIQUE (user_id, job_id),
    ADD INDEX idx_application_status (status),
    ADD INDEX idx_application_job (job_id);

-- Set password_hash per admin using Werkzeug's generate_password_hash before allowing login.
