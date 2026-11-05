import sqlite3
import tempfile
import unittest
from pathlib import Path

import app as portal
from werkzeug.security import generate_password_hash


class PortalRoutesTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        portal.app.config.update(
            TESTING=True,
            SECRET_KEY="test-only-secret",
            DATABASE=str(Path(self.temp_dir.name) / "test.sqlite3"),
        )
        self.client = portal.app.test_client()
        connection = portal.get_db()
        connection.execute(
            "INSERT INTO Admin (name,email,password_hash,role) VALUES (?,?,?,'admin')",
            ("Test Admin", "admin@example.com", generate_password_hash("correct-password", method="pbkdf2:sha256")),
        )
        connection.execute(
            "INSERT INTO Employer (employee_id,company_name,email,department) VALUES (2,?,?,?)",
            ("Example Co", "hr@example.com", "Hiring"),
        )
        connection.execute(
            "INSERT INTO JobSeeker (user_id,first_name,last_name,email,skills) VALUES (31,?,?,?,?)",
            ("Candidate", "One", "candidate@example.com", "Python, SQL"),
        )
        connection.execute(
            "INSERT INTO Job (job_id,title,description,location,posted_date,salary,age,employer_id) VALUES (21,?,?,?,?,?,?,2)",
            ("Engineer", "Build systems", "Remote", "2026-11-05", 1000, 0),
        )
        connection.commit()
        connection.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_login_checks_password_hash_and_sets_admin_role(self):
        response = self.client.post("/", data={"email": "admin@example.com", "password": "correct-password"})
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as current_session:
            self.assertEqual(current_session["role"], "admin")
            self.assertEqual(current_session["user_id"], 1)

    def test_admin_can_create_job(self):
        with self.client.session_transaction() as current_session:
            current_session.update(user_id=1, role="admin")
        response = self.client.post("/addjob", data={
            "job_id": "22", "title": "Designer", "description": "Design products",
            "location": "Bengaluru", "salary": "1000", "degree": "", "age": "0", "employer_id": "2",
        })
        self.assertEqual(response.status_code, 302)
        connection = sqlite3.connect(portal.app.config["DATABASE"])
        created = connection.execute("SELECT title FROM Job WHERE job_id=22").fetchone()
        connection.close()
        self.assertEqual(created[0], "Designer")

    def test_registered_applicant_can_submit_application(self):
        response = self.client.post("/jobs/21/apply", data={"email": "candidate@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Application submitted", response.data)
        connection = sqlite3.connect(portal.app.config["DATABASE"])
        submitted = connection.execute(
            "SELECT user_id,job_id,status FROM Application"
        ).fetchone()
        connection.close()
        self.assertEqual(submitted, (31, 21, "Pending"))

    def test_job_search_and_pagination_use_sqlite(self):
        response = self.client.get("/jobs?q=Eng&per_page=10&page=1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Engineer", response.data)

    def test_duplicate_application_is_rejected(self):
        self.client.post("/jobs/21/apply", data={"email": "candidate@example.com"})
        response = self.client.post("/jobs/21/apply", data={"email": "candidate@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"already applied", response.data)

    def test_applicant_history_and_csv_exports(self):
        connection = sqlite3.connect(portal.app.config["DATABASE"])
        connection.execute(
            "INSERT INTO Application (applied_date,user_id,job_id) VALUES ('2026-11-05',31,21)"
        )
        connection.commit()
        connection.close()
        with self.client.session_transaction() as current_session:
            current_session.update(user_id=1, role="admin")

        detail = self.client.get("/jobseekers/31")
        applications = self.client.get("/applications")
        application_export = self.client.get("/export/applications.csv")
        applicant_export = self.client.get("/export/applicants.csv")
        self.assertEqual(detail.status_code, 200)
        self.assertIn(b"Application history", detail.data)
        self.assertEqual(applications.status_code, 200)
        self.assertIn(b"Engineer", applications.data)
        self.assertIn(b"text/csv", application_export.content_type.encode())
        self.assertIn(b"candidate@example.com", application_export.data)
        self.assertIn(b"candidate@example.com", applicant_export.data)


if __name__ == "__main__":
    unittest.main()
