from database.db import db
from sqlalchemy.sql import func


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    project_id = db.Column(db.String(50), db.ForeignKey('projects.project_id'), nullable=False)  # ✅ Fixed ForeignKey
    status = db.Column(db.Integer, default=0)  # 0 = Not Started, 1 = Completed

    # ✅ Relationships
    project = db.relationship('Project', back_populates='tasks')
    subtasks = db.relationship('Subtask', back_populates='task', cascade="all, delete-orphan")
    

class Subtask(db.Model):
    __tablename__ = 'subtasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    employee_id = db.Column(db.String(50), db.ForeignKey('employees.employee_id'), nullable=True)  # ✅ Fixed ForeignKey
    status = db.Column(db.Integer, default=0)  # 0 = Not Started, 1 = Completed

    # ✅ Relationships
    task = db.relationship('Task', back_populates='subtasks')
    employee = db.relationship('Employee', back_populates='subtasks')
    milestones = db.relationship('Milestone', back_populates='subtask', cascade="all, delete-orphan")
    assignments = db.relationship('Assignment', back_populates='subtask')

   
class Milestone(db.Model):
    __tablename__ = 'milestones'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subtask_id = db.Column(db.Integer, db.ForeignKey('subtasks.id'), nullable=False)
    milestone_name = db.Column(db.String(255), nullable=False)  # ✅ Updated to match SQL column name
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)  # ✅ Initially NULL
    status = db.Column(db.Integer, default=0)  # 0 = Not Completed, 1 = Completed
    completed_at = db.Column(db.TIMESTAMP, nullable=True, default=None)  # ✅ Default NULL

    # ✅ Relationships
    subtask = db.relationship('Subtask', back_populates='milestones')
    