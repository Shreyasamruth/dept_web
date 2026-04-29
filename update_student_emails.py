import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app, db
from models import User

with app.app_context():
    students = User.query.filter_by(role='student').all()
    updated = 0
    for student in students:
        if not student.email:
            student.email = f"{student.username.lower()}@gmail.com"
            updated += 1
    
    db.session.commit()
    print(f"Successfully updated emails for {updated} students.")
