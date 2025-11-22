-- Insert JobSeeker
INSERT INTO JobSeeker (user_id, first_name, middle_name, last_name, email, skills, resume)
VALUES (1, 'Alice', 'B', 'Smith', 'alice@example.com', 'Python,SQL', 'alice_resume.pdf');

-- Insert Employer
INSERT INTO Employer (employee_id, company_name, email, department)
VALUES (1, 'TechCorp', 'hr@techcorp.com', 'IT');

-- Insert Job
INSERT INTO Job (job_id, title, description, location, posted_date, salary, degree, age, employer_id)
VALUES (1, 'Data Scientist', 'ML projects', 'Bangalore', '2025-11-05', 85000, 'MSc', 22, 1);

-- Insert Application
INSERT INTO Application (application_id, applied_date, status, user_id, job_id)
VALUES (1, '2025-11-06', 'Pending', 1, 1);

-- Insert Admin
INSERT INTO Admin (admin_id, name, email)
VALUES (1, 'Rahul', 'rahul.admin@jobportal.com');

-- Insert Interview
INSERT INTO Interview (interview_id, application_id, date, mode, feedback)
VALUES (1, 1, '2025-11-10', 'Online', 'Awaiting Interview');



