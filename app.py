import os
import re
import csv
import sqlite3
from io import StringIO
from datetime import date
from functools import wraps
from pathlib import Path

from flask import Flask, Response, redirect, render_template, request, session, url_for
import click
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", ""),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    DATABASE=os.environ.get("DATABASE_PATH", str(Path(__file__).with_name("instance") / "job_application_portal.sqlite3")),
)


def get_db():
    database_path = Path(app.config["DATABASE"])
    if str(database_path) != ":memory:":
        database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    if not connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='Admin'").fetchone():
        schema_path = Path(__file__).with_name("schema.sql")
        connection.executescript(schema_path.read_text(encoding="utf-8"))
    return connection


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            return "Forbidden", 403
        return view(*args, **kwargs)
    return wrapped


def valid_email(value):
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value or ""))


@app.cli.command("init-db")
def init_db_command():
    """Create the SQLite database schema if needed."""
    connection = get_db()
    connection.close()
    click.echo("SQLite database is ready.")


@app.cli.command("create-admin")
@click.option("--name", prompt=True)
@click.option("--email", prompt=True)
@click.password_option()
def create_admin_command(name, email, password):
    """Create an administrator account."""
    email = email.strip().lower()
    if not name.strip() or not valid_email(email):
        raise click.ClickException("Enter a name and valid email address.")
    connection = get_db()
    try:
        connection.execute(
            "INSERT INTO Admin (name,email,password_hash,role) VALUES (?,?,?,'admin')",
            (name.strip(), email, generate_password_hash(password, method="pbkdf2:sha256")),
        )
        connection.commit()
    except sqlite3.IntegrityError:
        raise click.ClickException("An account with that email already exists.")
    finally:
        connection.close()
    click.echo(f"Admin account created for {email}.")


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not valid_email(email) or not password:
            return render_template('login.html', error="Enter a valid email and password."), 400
        connection = get_db()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT admin_id, name, email, password_hash, role FROM Admin WHERE email = ?", (email,))
            admin = cursor.fetchone()
            cursor.close()
        finally:
            connection.close()
        if not admin or not admin['password_hash'] or not check_password_hash(admin['password_hash'], password):
            return render_template('login.html', error="Invalid email or password."), 401
        if admin['role'] != 'admin':
            return render_template('login.html', error="This account does not have admin access."), 403
        session.clear()
        session['user_id'] = admin['admin_id']
        session['user'] = admin['name']
        session['role'] = admin['role']
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/dashboard')
@admin_required
def dashboard():
    connection = get_db()
    try:
        cursor = connection.cursor()
        cursor.execute("""SELECT
            (SELECT COUNT(*) FROM Job) AS total_jobs,
            (SELECT COUNT(*) FROM JobSeeker) AS total_applicants,
            (SELECT COUNT(*) FROM Application) AS total_applications""")
        totals = cursor.fetchone()
        cursor.execute("SELECT status, COUNT(*) AS total FROM Application GROUP BY status ORDER BY status")
        statuses = cursor.fetchall()
        cursor.close()
    finally:
        connection.close()
    return render_template('dashboard.html', totals=totals, statuses=statuses)


@app.route('/jobs')
def jobs():
    term = request.args.get('q', '').strip()[:100]
    try:
        page = max(1, int(request.args.get('page', '1')))
        per_page = int(request.args.get('per_page', '10'))
    except ValueError:
        page, per_page = 1, 10
    if per_page not in (10, 20):
        per_page = 10
    connection = get_db()
    try:
        cursor = connection.cursor()
        where = "WHERE j.title LIKE ? OR j.location LIKE ? OR e.company_name LIKE ?" if term else ""
        params = (f"%{term}%",) * 3 if term else ()
        cursor.execute(f"SELECT COUNT(*) AS total FROM Job j JOIN Employer e ON e.employee_id = j.employer_id {where}", params)
        total = cursor.fetchone()['total']
        pages = max(1, (total + per_page - 1) // per_page)
        page = min(page, pages)
        cursor.execute(f"""SELECT j.job_id,j.title,j.description,j.location,j.posted_date,j.salary,
            e.company_name FROM Job j JOIN Employer e ON e.employee_id = j.employer_id
            {where} ORDER BY j.posted_date DESC,j.job_id DESC LIMIT ? OFFSET ?""", params + (per_page, (page - 1) * per_page))
        rows = cursor.fetchall()
        cursor.close()
        return render_template('jobs.html', jobs=rows, q=term, page=page, pages=pages,
                               per_page=per_page, total=total)
    finally:
        connection.close()


@app.route('/jobs/<int:job_id>/apply', methods=['GET', 'POST'])
def apply_job(job_id):
    connection = get_db()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT job_id,title,location FROM Job WHERE job_id=?", (job_id,))
        job = cursor.fetchone()
        cursor.close()
        if not job:
            return "Job not found", 404
        error = None
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            if not valid_email(email):
                error = "Enter a valid email address."
            else:
                cursor = connection.cursor()
                cursor.execute("SELECT user_id FROM JobSeeker WHERE email=?", (email,))
                seeker = cursor.fetchone()
                cursor.close()
                if not seeker:
                    error = "No applicant account uses that email. Contact the portal administrator to register."
                else:
                    try:
                        cursor = connection.cursor()
                        cursor.execute("INSERT INTO Application (applied_date,status,user_id,job_id) VALUES (?,'Pending',?,?)", (date.today(), seeker['user_id'], job_id))
                        connection.commit()
                        cursor.close()
                        return render_template('apply.html', job=job, success=True)
                    except sqlite3.IntegrityError:
                        connection.rollback()
                        error = "This applicant has already applied for this job."
        return render_template('apply.html', job=job, error=error)
    finally:
        connection.close()


@app.route('/jobseekers/<int:user_id>')
@admin_required
def applicant_detail(user_id):
    connection = get_db()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT user_id,first_name,middle_name,last_name,email,skills,resume FROM JobSeeker WHERE user_id=?", (user_id,))
        seeker = cursor.fetchone()
        if not seeker:
            return "Applicant not found", 404
        cursor.execute("""SELECT a.application_id,a.applied_date,a.status,j.job_id,j.title,j.location
            FROM Application a JOIN Job j ON j.job_id=a.job_id
            WHERE a.user_id=? ORDER BY a.applied_date DESC,a.application_id DESC""", (user_id,))
        history = cursor.fetchall()
        cursor.execute("""SELECT i.interview_id,i.date,i.mode,i.feedback,a.job_id,j.title
            FROM Interview i JOIN Application a ON a.application_id=i.application_id
            JOIN Job j ON j.job_id=a.job_id WHERE a.user_id=? ORDER BY i.date DESC""", (user_id,))
        interviews = cursor.fetchall()
        cursor.close()
        return render_template('applicant_detail.html', seeker=seeker, history=history, interviews=interviews)
    finally:
        connection.close()


def csv_response(filename, headers, rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return Response('\ufeff' + output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="{filename}"'})


@app.route('/export/applications.csv')
@admin_required
def export_applications():
    connection = get_db()
    try:
        cursor = connection.cursor()
        cursor.execute("""SELECT a.application_id,TRIM(COALESCE(js.first_name,'') || ' ' || COALESCE(js.middle_name,'') || ' ' || COALESCE(js.last_name,'')),
            js.email,js.skills,j.title,j.location,a.status,a.applied_date
            FROM Application a JOIN JobSeeker js ON js.user_id=a.user_id
            JOIN Job j ON j.job_id=a.job_id ORDER BY a.applied_date DESC,a.application_id DESC""")
        rows = cursor.fetchall()
        cursor.close()
        return csv_response('applications.csv', ('Application ID','Applicant','Email','Skills','Job','Location','Status','Applied Date'), rows)
    finally:
        connection.close()


@app.route('/export/applicants.csv')
@admin_required
def export_applicants():
    connection = get_db()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT user_id,first_name,middle_name,last_name,email,skills,resume FROM JobSeeker ORDER BY last_name,first_name")
        rows = cursor.fetchall()
        cursor.close()
        return csv_response('applicants.csv', ('Applicant ID','First Name','Middle Name','Last Name','Email','Skills','Resume'), rows)
    finally:
        connection.close()


@app.route('/addjob', methods=['GET', 'POST'])
@admin_required
def addjob():
    connection = get_db()
    error = None
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT employee_id, company_name, department FROM Employer ORDER BY company_name")
        employers = cursor.fetchall()
        cursor.close()
        if request.method == 'POST':
            try:
                job_id = int(request.form.get('job_id', ''))
                title = request.form.get('title', '').strip()
                description = request.form.get('description', '').strip()
                location = request.form.get('location', '').strip()
                salary = float(request.form.get('salary', '0') or 0)
                degree = request.form.get('degree', '').strip()
                age = int(request.form.get('age', '0') or 0)
                employer_id = int(request.form.get('employer_id', ''))
                if not all((title, description, location)) or salary < 0 or age < 0:
                    raise ValueError("Complete required fields and use non-negative salary and age.")
                cursor = connection.cursor()
                cursor.execute("INSERT INTO Job (job_id,title,description,location,posted_date,salary,degree,age,employer_id) VALUES (?,?,?,?,?,?,?,?,?)", (job_id,title,description,location,date.today(),salary,degree,age,employer_id))
                connection.commit()
                cursor.close()
                return redirect(url_for('dashboard'))
            except (ValueError, TypeError, sqlite3.Error) as exc:
                connection.rollback()
                error = str(exc) if isinstance(exc, ValueError) else "Could not save the job. Check the ID and employer, then try again."
        return render_template('addjob.html', employers=employers, error=error)
    finally:
        connection.close()


@app.route('/jobseekers')
@admin_required
def jobseekers():
    connection = get_db()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT user_id, first_name, middle_name, last_name, email, skills FROM JobSeeker ORDER BY last_name, first_name")
        rows = cursor.fetchall()
        cursor.close()
        return render_template('jobseekers.html', jobseekers=rows)
    finally:
        connection.close()


@app.route('/addjobseeker', methods=['GET', 'POST'])
@admin_required
def addjobseeker():
    error = None
    if request.method == 'POST':
        fields = {key: request.form.get(key, '').strip() for key in ('first_name','middle_name','last_name','email','skills','resume')}
        fields['email'] = fields['email'].lower()
        if not fields['first_name'] or not fields['last_name'] or not fields['skills'] or not valid_email(fields['email']):
            error = "First name, last name, skills, and a valid email are required."
        else:
            connection = get_db()
            try:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO JobSeeker (user_id,first_name,middle_name,last_name,email,skills,resume) VALUES (?,?,?,?,?,?,?)", (int(request.form.get('user_id', '')), fields['first_name'], fields['middle_name'] or None, fields['last_name'], fields['email'], fields['skills'], fields['resume'] or None))
                connection.commit()
                cursor.close()
                return redirect(url_for('jobseekers'))
            except (ValueError, sqlite3.Error):
                connection.rollback()
                error = "Could not save the job seeker. Check that the ID and email are unique."
            finally:
                connection.close()
    return render_template('addjobseeker.html', error=error)


@app.route('/applications', methods=['GET', 'POST'])
@admin_required
def applications():
    connection = get_db()
    error = None
    try:
        if request.method == 'POST':
            application_id = request.form.get('application_id', '').strip()
            status = request.form.get('status', '')
            allowed = {'Pending', 'Shortlisted', 'Interview', 'Selected', 'Rejected'}
            if status not in allowed:
                error = "Choose a valid application status."
            else:
                cursor = connection.cursor()
                cursor.execute("UPDATE Application SET status = ? WHERE application_id = ?", (status, application_id))
                if cursor.rowcount == 0:
                    error = "Application was not found."
                else:
                    connection.commit()
                cursor.close()
        cursor = connection.cursor()
        cursor.execute("""SELECT a.application_id, a.user_id, a.job_id, a.applied_date, a.status,
            TRIM(COALESCE(js.first_name,'') || ' ' || COALESCE(js.middle_name,'') || ' ' || COALESCE(js.last_name,'')) AS applicant_name,
            j.title AS job_title
            FROM Application a JOIN JobSeeker js ON js.user_id = a.user_id
            JOIN Job j ON j.job_id = a.job_id ORDER BY a.applied_date DESC, a.application_id DESC""")
        rows = cursor.fetchall()
        cursor.close()
        return render_template('applications.html', applications=rows, error=error,
                               statuses=('Pending','Shortlisted','Interview','Selected','Rejected'))
    finally:
        connection.close()


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    if not app.config['SECRET_KEY']:
        raise RuntimeError('Set FLASK_SECRET_KEY before starting the application.')
    app.run(debug=os.environ.get('FLASK_DEBUG', '0') == '1')
