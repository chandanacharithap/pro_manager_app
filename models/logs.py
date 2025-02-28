from database.db import db
from datetime import datetime

class AssignmentLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    employee_id = db.Column(db.String(100), db.ForeignKey('employees.employee_id'))
    log_message = db.Column(db.Text, nullable=False)
