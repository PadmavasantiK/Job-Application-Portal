from flask import Flask, render_template, request, redirect, session
import mysql.connector
from datetime import date

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this for production

# --- Update these with your actual MySQL credentials ---
db = mysql.connector.connect(
    host="localhost",
    user="project",                 # <-- Your MySQL username here
    password="p@dm@*513",     # <-- Your MySQL password here
    database="JobApplicationPortal"
)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        session['user'] = email
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template('dashboard.html')

@app.route('/addjob', methods=['GET', 'POST'])
def addjob():
    if 'user' not in session:
        return redirect('/')
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT employee_id, company_name, department FROM Employer")
    employers = cursor.fetchall()
    cursor.close()
    if request.method == 'POST':
        try:
            job_id = int(request.form['job_id'])
            title = request.form['title']
            description = request.form['description']
            location = request.form['location']
            salary = float(request.form.get('salary', 0))
            degree = request.form['degree']
            age = int(request.form.get('age', 0))
            employer_id = int(request.form['employer_id'])
            posted_date = date.today()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO Job (job_id, title, description, location, posted_date, salary, degree, age, employer_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (job_id, title, description, location, posted_date, salary, degree, age, employer_id)
            )
            db.commit()
            cursor.close()
            return redirect('/dashboard')
        except Exception as e:
            error_msg = f"Error: {str(e)}. Are you using a unique job ID and a valid Employer ID?"
            return render_template('addjob.html', employers=employers, error=error_msg)
    return render_template('addjob.html', employers=employers)

@app.route('/jobseekers')
def jobseekers():
    if 'user' not in session:
        return redirect('/')
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM JobSeeker")
    jobseekers = cursor.fetchall()
    cursor.close()
    return render_template('jobseekers.html', jobseekers=jobseekers)

@app.route('/addjobseeker', methods=['GET', 'POST'])
def addjobseeker():
    if 'user' not in session:
        return redirect('/')
    if request.method == 'POST':
        try:
            user_id = int(request.form['user_id'])
            fname = request.form['first_name']
            mname = request.form['middle_name']
            lname = request.form['last_name']
            email = request.form['email']
            skills = request.form['skills']
            resume = request.form['resume']
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO JobSeeker (user_id, first_name, middle_name, last_name, email, skills, resume) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (user_id, fname, mname, lname, email, skills, resume)
            )
            db.commit()
            cursor.close()
            return redirect('/jobseekers')
        except Exception as e:
            error_msg = f"Error: {str(e)}. Make sure your user_id and email are unique."
            return render_template('addjobseeker.html', error=error_msg)
    return render_template('addjobseeker.html')



@app.route('/applications')
def applications():
    if 'user' not in session:
        return redirect('/')
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Application")
    applications = cursor.fetchall()
    cursor.close()
    return render_template('applications.html', applications=applications)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
