PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS JobSeeker (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    middle_name TEXT,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    skills TEXT NOT NULL,
    resume TEXT
);

CREATE TABLE IF NOT EXISTS Employer (
    employee_id INTEGER PRIMARY KEY,
    company_name TEXT NOT NULL,
    email TEXT COLLATE NOCASE UNIQUE,
    department TEXT
);

CREATE TABLE IF NOT EXISTS Job (
    job_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT NOT NULL,
    posted_date TEXT NOT NULL,
    salary NUMERIC CHECK (salary IS NULL OR salary >= 0),
    degree TEXT,
    age INTEGER CHECK (age IS NULL OR age >= 0),
    employer_id INTEGER NOT NULL,
    FOREIGN KEY (employer_id) REFERENCES Employer(employee_id)
);
CREATE INDEX IF NOT EXISTS idx_job_employer ON Job(employer_id);
CREATE INDEX IF NOT EXISTS idx_job_posted_date ON Job(posted_date);

CREATE TABLE IF NOT EXISTS Application (
    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
    applied_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending'
        CHECK (status IN ('Pending','Shortlisted','Interview','Selected','Rejected')),
    user_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES JobSeeker(user_id),
    FOREIGN KEY (job_id) REFERENCES Job(job_id),
    UNIQUE (user_id, job_id)
);
CREATE INDEX IF NOT EXISTS idx_application_status ON Application(status);
CREATE INDEX IF NOT EXISTS idx_application_job ON Application(job_id);

CREATE TABLE IF NOT EXISTS Admin (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT,
    role TEXT NOT NULL DEFAULT 'admin' CHECK (role = 'admin')
);

CREATE TABLE IF NOT EXISTS Interview (
    interview_id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    date TEXT,
    mode TEXT,
    feedback TEXT,
    FOREIGN KEY (application_id) REFERENCES Application(application_id)
);
