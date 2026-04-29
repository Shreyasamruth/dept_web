import sys
import os
import csv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app, db
from models import Student

csv_file = r"d:\class data\student_list.csv"

students = []
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader) # skip header
    for row in reader:
        if len(row) >= 2:
            usn = row[0].strip()
            name = row[1].strip()
            students.append({'usn': usn, 'name': name})

students.sort(key=lambda x: x['usn'])

with app.app_context():
    db.create_all()
    added = 0
    for student_data in students:
        usn = student_data['usn']
        name = student_data['name']
        email = f"{usn.lower()}@gmail.com"
        
        existing = Student.query.filter_by(usn=usn).first()
        if not existing:
            new_student = Student(usn=usn, name=name, email=email)
            db.session.add(new_student)
            added += 1
            
    db.session.commit()
    print(f"Successfully added {added} students to the new database.")
