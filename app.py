import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from werkzeug.utils import secure_filename
from models import db, Student, Admin, Certificate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USERNAME = 'shryasmine12@gmail.com'
MAIL_PASSWORD = 'kjkxgeegjgxbuaqs'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db.init_app(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

def send_otp(to_email, otp):
    msg = MIMEText(f"Hello,\n\nYour OTP for DEPT OF AI is: {otp}\n\nDo not share this code with anyone.")
    msg['Subject'] = 'DEPT OF AI OTP'
    msg['From'] = MAIL_USERNAME
    msg['To'] = to_email

    print(f"\n{'='*40}")
    print(f"DEBUG: OTP for {to_email} is {otp}")
    print(f"{'='*40}\n")

    try:
        server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# ----- PUBLIC & LANDING ROUTES -----

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ----- STUDENT ROUTES -----

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        usn = request.form['usn'].strip().upper()
        
        student = Student.query.filter_by(usn=usn).first()
        if student:
            otp = ''.join(random.choices(string.digits, k=6))
            session['pending_student'] = {
                'id': student.id,
                'usn': student.usn,
                'name': student.name,
                'email': student.email,
                'otp': otp
            }
            if send_otp(student.email, otp):
                flash(f'An OTP has been sent to {student.email}.', 'success')
                return redirect(url_for('student_verify_otp'))
            else:
                flash('Failed to send OTP email. Check server configuration.', 'error')
        else:
            flash('USN not found. Please contact administration.', 'error')
            
    return render_template('student_login.html')

@app.route('/student_verify_otp', methods=['GET', 'POST'])
def student_verify_otp():
    if 'pending_student' not in session:
        return redirect(url_for('student_login'))
        
    if request.method == 'POST':
        user_otp = request.form['otp'].strip()
        pending = session['pending_student']
        
        if user_otp == pending['otp']:
            session['student_id'] = pending['id']
            session['student_usn'] = pending['usn']
            session['student_name'] = pending['name']
            session.pop('pending_student', None)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('student_portal'))
        else:
            flash('Invalid OTP. Please try again.', 'error')
            
    return render_template('student_verify_otp.html')

@app.route('/student_logout')
def student_logout():
    session.pop('student_id', None)
    session.pop('student_usn', None)
    session.pop('student_name', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('landing'))

@app.route('/student_portal', methods=['GET', 'POST'])
def student_portal():
    if 'student_id' not in session:
        flash('Please login to upload certificates.', 'error')
        return redirect(url_for('student_login'))

    student_id = session['student_id']
    student = db.session.get(Student, student_id)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        file = request.files.get('certificate')
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{student_id}_{int(datetime.utcnow().timestamp())}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            new_cert = Certificate(student_id=student_id, title=title, description=description, file_path=unique_filename)
            db.session.add(new_cert)
            db.session.commit()
            flash('Certificate uploaded successfully!', 'success')
            
            return redirect(url_for('student_view', usn=student.usn))
        else:
            flash('Invalid file. Only PDF files are allowed.', 'error')
            return redirect(url_for('student_portal'))
            
    return render_template('index.html', user=student)

@app.route('/student/<usn>')
def student_view(usn):
    if not (session.get('admin_id') or session.get('student_usn') == usn):
        flash('Unauthorized access.', 'error')
        return redirect(url_for('landing'))

    student = Student.query.filter_by(usn=usn).first_or_404()
    certificates = Certificate.query.filter_by(student_id=student.id).order_by(Certificate.upload_date.desc()).all()
    return render_template('student_dashboard.html', user=student, certificates=certificates)

@app.route('/edit_certificate/<int:cert_id>', methods=['GET', 'POST'])
def edit_certificate(cert_id):
    cert = db.session.get(Certificate, cert_id)
    if not cert:
        return redirect(url_for('landing'))
    student = db.session.get(Student, cert.student_id)
    
    if not (session.get('admin_id') or session.get('student_id') == student.id):
        flash('Unauthorized access.', 'error')
        return redirect(url_for('landing'))

    if request.method == 'POST':
        cert.title = request.form['title']
        cert.description = request.form.get('description', '')
        
        file = request.files.get('certificate')
        if file and file.filename != '':
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{student.id}_{int(datetime.utcnow().timestamp())}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], cert.file_path)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                    
                cert.file_path = unique_filename
            else:
                flash('Invalid file. Only PDF files are allowed.', 'error')
                return redirect(url_for('edit_certificate', cert_id=cert.id))
                
        db.session.commit()
        flash('Certificate updated successfully!', 'success')
        return redirect(url_for('student_view', usn=student.usn))
        
    return render_template('edit_certificate.html', cert=cert, user=student)

@app.route('/delete_certificate/<int:cert_id>', methods=['POST'])
def delete_certificate(cert_id):
    cert = db.session.get(Certificate, cert_id)
    if not cert:
        return redirect(url_for('landing'))
    student = db.session.get(Student, cert.student_id)
    
    if not (session.get('admin_id') or session.get('student_id') == student.id):
        flash('Unauthorized access.', 'error')
        return redirect(url_for('landing'))

    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], cert.file_path)
    if os.path.exists(old_file_path):
        os.remove(old_file_path)
    db.session.delete(cert)
    db.session.commit()
    flash('Certificate deleted successfully!', 'success')
    
    return redirect(url_for('student_view', usn=student.usn))

# ----- ADMIN ROUTES -----

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'error')
            
    return render_template('admin_login.html')

@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if Admin.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('admin_register'))
            
        if Admin.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('admin_register'))
            
        otp = ''.join(random.choices(string.digits, k=6))
        session['pending_admin'] = {
            'username': username,
            'email': email,
            'password': password, 
            'otp': otp
        }
        
        if send_otp(email, otp):
            flash(f'An OTP has been sent to {email}. Please verify.', 'success')
            return redirect(url_for('verify_otp'))
        else:
            flash('Failed to send OTP email. Check server configuration.', 'error')
            
    return render_template('admin_register.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'pending_admin' not in session:
        return redirect(url_for('admin_register'))
        
    if request.method == 'POST':
        user_otp = request.form['otp'].strip()
        pending = session['pending_admin']
        
        if user_otp == pending['otp']:
            new_admin = Admin(username=pending['username'], email=pending['email'])
            new_admin.set_password(pending['password'])
            db.session.add(new_admin)
            db.session.commit()
            
            session.pop('pending_admin', None)
            flash('Admin account created successfully! Please login.', 'success')
            return redirect(url_for('admin_login'))
        else:
            flash('Invalid OTP. Please try again.', 'error')
            
    return render_template('verify_otp.html')

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Please login to access the admin dashboard', 'error')
        return redirect(url_for('admin_login'))
        
    students = Student.query.order_by(Student.usn).all()
    certificates = Certificate.query.all()
    
    student_data = []
    for student in students:
        student_certs = [c for c in certificates if c.student_id == student.id]
        student_data.append({
            'user': student,
            'certificates': student_certs
        })
        
    return render_template('admin_dashboard.html', student_data=student_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
