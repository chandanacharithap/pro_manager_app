from database.db import db

class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)  # ✅ Ensured consistency
    name = db.Column(db.String(255), nullable=False)
    skills = db.Column(db.Text, nullable=False)

    # ✅ Relationships
    assignments = db.relationship('Assignment', back_populates='employee')
    subtasks = db.relationship('Subtask', back_populates='employee')
