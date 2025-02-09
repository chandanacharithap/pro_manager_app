from database.db import db

class Project(db.Model):
    __tablename__ = "projects"

    project_id = db.Column(db.String(50), primary_key=True)
    description = db.Column(db.Text, nullable=False)

    # ✅ Relationship with Task
    tasks = db.relationship("Task", back_populates="project", lazy="dynamic", cascade="all, delete-orphan")
    
    # ✅ Relationship with Assignment
    assignments = db.relationship("Assignment", back_populates="project", lazy="dynamic", cascade="all, delete-orphan")
