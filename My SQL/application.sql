USE JobApplicationPortal;
SELECT a.application_id, js.first_name, js.last_name, j.title, a.status
FROM Application a
JOIN JobSeeker js ON a.user_id = js.user_id
JOIN Job j ON a.job_id = j.job_id;

SELECT e.company_name, j.title, j.location, j.salary
FROM Job j
JOIN Employer e ON j.employer_id = e.employee_id;

SELECT i.interview_id, a.application_id, js.first_name, js.last_name, i.date, i.mode, i.feedback
FROM Interview i
JOIN Application a ON i.application_id = a.application_id
JOIN JobSeeker js ON a.user_id = js.user_id;

UPDATE Application
SET status = 'Selected'
WHERE application_id = 1;

SELECT * FROM Application;