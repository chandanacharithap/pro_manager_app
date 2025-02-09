from database.db import db

class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.String(50), db.ForeignKey('employees.employee_id'), nullable=False)  # ✅ Fixed ForeignKey
    project_id = db.Column(db.String(50), db.ForeignKey('projects.project_id'), nullable=False)  # ✅ Fixed ForeignKey
    subtask_id = db.Column(db.Integer, db.ForeignKey('subtasks.id'), nullable=True)  # Can be NULL initially
    status = db.Column(db.Integer, default=0)  # 0 = In Progress, 1 = Completed

    # ✅ Relationships
    employee = db.relationship('Employee', back_populates='assignments')
    project = db.relationship('Project', back_populates='assignments')
    subtask = db.relationship('Subtask', back_populates='assignments')