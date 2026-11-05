# Job Application Portal

A Flask job portal backed by SQLite. SQLite is included with Python, so you do not need to install or run a database server.

## Features

- Admin login with hashed passwords and admin-only management pages
- Add and browse jobs; search by title, location, or company with pagination
- Register job seekers and accept applications from registered applicant emails
- Track application statuses and view applicant application/interview history
- Dashboard analytics and CSV exports for applicants and applications
- Automated tests using a temporary SQLite database

## Setup

1. Install Python 3.9 or newer.
2. From this project directory, install Flask:

   ```sh
   python -m pip install -r requirements.txt
   ```

3. Initialize the database and create the first admin account:

   ```sh
   flask --app app init-db
   flask --app app create-admin
   ```

   The admin command prompts for a name, email, and password. SQLite creates `instance/job_application_portal.sqlite3` automatically.

4. Set a session secret and run the app:

   ```sh
   export FLASK_SECRET_KEY="replace-this-with-a-long-random-value"
   flask --app app run
   ```

   Open http://127.0.0.1:5000. Public job listings are at `/jobs`.

## Tests

Run the automated route tests with:

```sh
python -m unittest discover -s tests -v
```

The tests create and remove a temporary SQLite database; they do not change the app's database.

## Database files

`schema.sql` is the SQLite schema used by the Flask app. `My SQL/Database.sql` contains the same SQLite schema for convenience. Other historical files in `My SQL/` contain MySQL-specific examples and are not used by the app.
