-- functions
DETERMINISTIC
BEGIN
    DECLARE full_name VARCHAR(150);
    SELECT CONCAT(first_name, ' ', middle_name, ' ', last_name)
    INTO full_name
    FROM JobSeeker
    WHERE user_id = user_id;
    RETURN full_name;
END //
DELIMITER ;

DELIMITER //
CREATE FUNCTION CountApplications(user_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE total INT;
    SELECT COUNT(*) INTO total
    FROM Application
    WHERE user_id = user_id;
    RETURN total;
END //
DELIMITER ;

DELIMITER //
CREATE FUNCTION GetAverageSalary(emp_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE avg_salary DECIMAL(10,2);
    SELECT AVG(salary) INTO avg_salary
    FROM Job
    WHERE employer_id = emp_id;
    RETURN IFNULL(avg_salary, 0);
END //
DELIMITER ;
