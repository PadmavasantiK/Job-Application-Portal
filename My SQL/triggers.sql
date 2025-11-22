DELIMITER //
CREATE TRIGGER UpdateJobStatusAfterInterview
AFTER UPDATE ON Application
FOR EACH ROW
BEGIN
    IF NEW.status = 'Hired' THEN
        UPDATE Job
        SET status = 'Closed'
        WHERE job_id = NEW.job_id;
    END IF;
END //
DELIMITER ;

CREATE TABLE ApplicationLog (
    log_id INT PRIMARY KEY,
    application_id INT,
    action VARCHAR(100),
    timestamp DATETIME
);

DELIMITER //
CREATE TRIGGER LogApplicationInsert
AFTER INSERT ON Application
FOR EACH ROW
BEGIN
    INSERT INTO ApplicationLog (log_id, application_id, action, timestamp)
    VALUES (NULL, NEW.application_id, 'Application Submitted', NOW());
END //
DELIMITER ;

DELIMITER //
CREATE TRIGGER PreventDuplicateApplications
BEFORE INSERT ON Application
FOR EACH ROW
BEGIN
    IF (SELECT COUNT(*) FROM Application WHERE user_id = NEW.user_id AND job_id = NEW.job_id) > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Duplicate application not allowed';
    END IF;
END //
DELIMITER ;
