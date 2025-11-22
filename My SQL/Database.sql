CREATE DATABASE JobApplicationPortal;
USE JobApplicationPortal;

-- JobSeeker Table
CREATE TABLE JobSeeker (
    user_id INT PRIMARY KEY,
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE,
    skills VARCHAR(255),
    resume VARCHAR(255)
) ENGINE=InnoDB;

-- Employer Table
CREATE TABLE Employer (
    employee_id INT PRIMARY KEY,
    company_name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    department VARCHAR(100)
) ENGINE=InnoDB;

-- Job Table
CREATE TABLE Job (
    job_id INT PRIMARY KEY,
    title VARCHAR(100),
    description TEXT,
    location VARCHAR(100),
    posted_date DATE,
    salary DECIMAL(12,2),
    degree VARCHAR(100),
    age INT,
    employer_id INT,
    FOREIGN KEY (employer_id) REFERENCES Employer(employee_id)
) ENGINE=InnoDB;

-- Application Table
CREATE TABLE Application (
    application_id INT PRIMARY KEY,
    applied_date DATE,
    status VARCHAR(50),
    user_id INT,
    job_id INT,
    FOREIGN KEY (user_id) REFERENCES JobSeeker(user_id),
    FOREIGN KEY (job_id) REFERENCES Job(job_id)
) ENGINE=InnoDB;

-- Admin Table
CREATE TABLE Admin (
    admin_id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE
) ENGINE=InnoDB;

-- Interview Table
CREATE TABLE Interview (
    interview_id INT PRIMARY KEY,
    application_id INT,
    date DATE,
    mode VARCHAR(50),
    feedback TEXT,
    FOREIGN KEY (application_id) REFERENCES Application(application_id)
) ENGINE=InnoDB;
