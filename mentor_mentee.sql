-- Create the database
CREATE DATABASE IF NOT EXISTS mentor_mentee;
USE mentor_mentee;

-- Create Mentor table
CREATE TABLE Mentor (
    Mentor_ID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100),
    Department VARCHAR(100),
    Contact_Info VARCHAR(100)
);

-- Create Mentee table
CREATE TABLE Mentee (
    Mentee_ID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100),
    Mentor_ID INT,
    Academic_Details VARCHAR(255),
    Contact_Info VARCHAR(100),
    FOREIGN KEY (Mentor_ID) REFERENCES Mentor(Mentor_ID),
    UNIQUE (Mentee_ID)
);

-- Create Meeting table
CREATE TABLE Meeting (
    Meeting_ID INT PRIMARY KEY AUTO_INCREMENT,
    Mentor_ID INT,
    Mentee_ID INT,
    Date DATE,
    Time TIME,
    Agenda VARCHAR(255),
    Summary TEXT,
    FOREIGN KEY (Mentor_ID) REFERENCES Mentor(Mentor_ID),
    FOREIGN KEY (Mentee_ID) REFERENCES Mentee(Mentee_ID)
);

-- Create Meeting_Report table (corrected)
CREATE TABLE Meeting_Report (
    Report_ID INT PRIMARY KEY AUTO_INCREMENT,
    Meeting_ID INT,
    Mentor_ID INT,
    Report_Text TEXT,
    Report_Date DATE DEFAULT (CURRENT_DATE),    -- Corrected syntax
    FOREIGN KEY (Meeting_ID) REFERENCES Meeting(Meeting_ID),
    FOREIGN KEY (Mentor_ID) REFERENCES Mentor(Mentor_ID)
);

-- Create Notifications table
CREATE TABLE Notifications (
    Notification_ID INT PRIMARY KEY AUTO_INCREMENT,
    Mentee_ID INT,
    Message TEXT,
    Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Mentee_ID) REFERENCES Mentee(Mentee_ID)
);

-- Create stored procedures
DELIMITER //

CREATE PROCEDURE AddMeeting(
    IN mentor_id INT,
    IN mentee_id INT,
    IN meeting_date DATE,
    IN meeting_time TIME,
    IN agenda VARCHAR(255)
)
BEGIN
    INSERT INTO Meeting (Mentor_ID, Mentee_ID, Date, Time, Agenda)
    VALUES (mentor_id, mentee_id, meeting_date, meeting_time, agenda);
END;
//
DELIMITER ;

DELIMITER //
CREATE PROCEDURE GetStudentListAndCount(IN mentor_id INT)
BEGIN
    -- Display the list of students for the mentor
    SELECT Mentee_ID, Name, Academic_Details, Contact_Info
    FROM Mentee
    WHERE Mentor_ID = mentor_id;
    
    -- Display the total number of students assigned to the mentor
    SELECT COUNT(*) AS Student_Count
    FROM Mentee
    WHERE Mentor_ID = mentor_id;
END;
//
DELIMITER ;

DELIMITER //
CREATE PROCEDURE GetCompletedMeetingsCount(IN mentor_id INT)
BEGIN
    SELECT m.Mentee_ID, me.Name AS Mentee_Name, COUNT(meeting.Meeting_ID) AS Completed_Meetings_Count
    FROM Meeting meeting
    JOIN Mentee m ON m.Mentee_ID = meeting.Mentee_ID
    JOIN Mentor me ON me.Mentor_ID = m.Mentor_ID
    WHERE me.Mentor_ID = mentor_id
      AND meeting.Date < CURRENT_DATE
    GROUP BY m.Mentee_ID, me.Name
    ORDER BY Completed_Meetings_Count DESC;
END;
//
DELIMITER ;

DELIMITER //
CREATE PROCEDURE AddMeetingReport (
    IN meeting_id INT,
    IN mentor_id INT,
    IN report_text TEXT
)
BEGIN
    INSERT INTO Meeting_Report (Meeting_ID, Mentor_ID, Report_Text)
    VALUES (meeting_id, mentor_id, report_text);
END;
//
DELIMITER ;

DELIMITER //
CREATE PROCEDURE GetNotifications(IN mentee_id INT)
BEGIN
    SELECT Message, Date
    FROM Notifications
    WHERE Mentee_ID = mentee_id
    ORDER BY Date DESC;
END;

//
DELIMITER ;

DELIMITER //
-- Create trigger
CREATE TRIGGER NotifyStudentOnReschedule
AFTER UPDATE ON Meeting
FOR EACH ROW
BEGIN
    IF OLD.Date != NEW.Date OR OLD.Time != NEW.Time THEN
        INSERT INTO Notifications (Mentee_ID, Message)
        VALUES (NEW.Mentee_ID, CONCAT('Your meeting with mentor ', NEW.Mentor_ID, ' has been rescheduled to ', NEW.Date, ' at ', NEW.Time));
    END IF;
END;
//
DELIMITER ;

DELIMITER ;



DELIMITER //
CREATE PROCEDURE GetStudentListAndCount(IN p_mentor_id INT)
BEGIN
    SELECT 
        Mentee_ID,
        Name,
        Academic_Details,
        Contact_Info
    FROM Mentee
    WHERE Mentor_ID = p_mentor_id
    ORDER BY Name;
END //
DELIMITER ;


DROP PROCEDURE IF EXISTS GetNotifications;
DELIMITER //

CREATE PROCEDURE GetNotifications(IN p_user_id INT)
BEGIN
    SELECT 
        Message,
        Notification_Date AS Date
    FROM Notification
    WHERE Recipient_ID = p_user_id
    ORDER BY Notification_Date DESC;
END //

DELIMITER ;

DELIMITER //

CREATE PROCEDURE AssignStudentToMentor(
    IN p_student_name VARCHAR(255),
    IN p_student_details VARCHAR(255),
    IN p_student_contact VARCHAR(255),
    IN p_student_password VARCHAR(255)
)
BEGIN
    DECLARE v_mentor_id INT;
    
    -- Find the mentor with the least number of mentees
    SELECT Mentor_ID
    INTO v_mentor_id
    FROM (
        SELECT m.Mentor_ID, COUNT(me.Mentee_ID) AS mentee_count
        FROM Mentor m
        LEFT JOIN Mentee me ON m.Mentor_ID = me.Mentor_ID
        GROUP BY m.Mentor_ID
        ORDER BY mentee_count ASC
        LIMIT 1
    ) AS mentor_counts;
    
    -- Insert the new student and assign them to the mentor
    INSERT INTO Mentee (Name, Mentor_ID, Academic_Details, Contact_Info, Password)
    VALUES (p_student_name, v_mentor_id, p_student_details, p_student_contact, p_student_password);
END //

DELIMITER ;


DELIMITER //

CREATE PROCEDURE DeleteMeeting(
    IN p_meeting_id INT,
    IN p_mentor_id INT,
    OUT p_success BOOLEAN
)
BEGIN
    DECLARE v_meeting_exists INT;
    
    -- Check if meeting exists and belongs to the mentor
    SELECT COUNT(*) INTO v_meeting_exists
    FROM Meeting 
    WHERE Meeting_ID = p_meeting_id 
    AND Mentor_ID = p_mentor_id;
    
    IF v_meeting_exists > 0 THEN
        -- First delete any associated meeting reports
        DELETE FROM Meeting_Report 
        WHERE Meeting_ID = p_meeting_id;
        
        -- Then delete the meeting
        DELETE FROM Meeting 
        WHERE Meeting_ID = p_meeting_id 
        AND Mentor_ID = p_mentor_id;
        
        -- Add notification for mentee
        INSERT INTO Notifications (Mentee_ID, Message)
        SELECT Mentee_ID, CONCAT('Meeting scheduled for ', Date, ' at ', Time, ' has been cancelled by your mentor.')
        FROM Meeting
        WHERE Meeting_ID = p_meeting_id;
        
        SET p_success = TRUE;
    ELSE
        SET p_success = FALSE;
    END IF;
END //

DELIMITER ;