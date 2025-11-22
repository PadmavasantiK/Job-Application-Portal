-- procedures
DELIMITER //
CREATE PROCEDURE AddJob(
    IN p_job_id INT,
    IN p_description TEXT,
    IN p_title VARCHAR(100),
    IN p_location VARCHAR(100),
    IN p_salary DECIMAL(15,2),
    IN p_degree VARCHAR(100),
    IN p_age INT,
    IN p_employer_id INT,
    IN p_posted_date DATE
)
BEGIN
    INSERT INTO Job (job_id, description, title, location, salary, degree, age, employer_id, posted_date)
    VALUES (p_job_id, p_description, p_title, p_location, p_salary, p_degree, p_age, p_employer_id, p_posted_date);
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE UpdateApplicationStatus(
    IN p_application_id INT,
    IN p_status VARCHAR(50)
)
BEGIN
    UPDATE Application
    SET status = p_status
    WHERE application_id = p_application_id;
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE ScheduleInterview(
    IN p_interview_id INT,
    IN p_application_id INT,
    IN p_date DATE,
    IN p_mode VARCHAR(50)
)
BEGIN
    INSERT INTO Interview (interview_id, application_id, date, mode, feedback)
    VALUES (p_interview_id, p_application_id, p_date, p_mode, 'Pending Feedback');
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE RemoveHiredJobSeeker(IN p_user_id INT)
BEGIN
    DELETE FROM Interview WHERE application_id IN (SELECT application_id FROM Application WHERE user_id = p_user_id);
    DELETE FROM Application WHERE user_id = p_user_id;
    DELETE FROM JobSeeker WHERE user_id = p_user_id;
END //
DELIMITER ;
