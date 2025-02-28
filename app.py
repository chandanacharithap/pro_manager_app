import threading
import time
from flask import Flask, render_template, request, jsonify
from database.db import db
from flask_migrate import Migrate
from config import Config
from ai.task_generator import generate_tasks_from_description
from ai.task_assigner import ai_task_agent  #  AI Agent for task assignment
from datetime import datetime
from models.logs import AssignmentLog  #  Import the AssignmentLog model


#  Initialize Flask App
app = Flask(__name__)
app.config.from_object(Config)

#  Initialize Database
db.init_app(app)
migrate = Migrate(app, db)

#  Import Models AFTER db.init_app(app) to prevent circular imports
from models.employee import Employee
from models.project import Project
from models.task import Task, Subtask, Milestone
from models.assignment import Assignment

#  Ensure Flask app context is used properly
with app.app_context():
    db.create_all()

@app.route('/projects',methods=['POST','GET'])
def project_home():
    return render_template("projects.html")

@app.route('/employee_dashboard',methods=['POST','GET'])
def employee_home():
    return render_template("employees.html")

### --------------- 📌 PROJECT MANAGER APIs --------------- ###

@app.route('/api/generate_tasks/<string:project_id>', methods=['POST','GET'])
def generate_tasks(project_id):
    """Generate tasks using AI and assign initial subtasks."""
    result = generate_tasks_from_description(project_id)
    return jsonify(result)

@app.route('/api/assign_tasks', methods=['POST'])
def assign_tasks():
    """Use AI Agent to assign tasks dynamically."""
    result = ai_task_agent.assign_tasks()
    return jsonify(result)

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Fetch all projects."""
    projects = Project.query.all()
    return jsonify([{"project_id": p.project_id, "description": p.description} for p in projects])

@app.route('/api/projects', methods=['POST'])
def add_project():
    """Add a new project to the database."""
    data = request.json  # Get JSON data from request

    #  Validate input
    if not data or 'project_id' not in data or 'description' not in data:
        return jsonify({"error": "Missing project_id or description"}), 400

    #  Check if project ID already exists
    existing_project = Project.query.filter_by(project_id=data['project_id']).first()
    if existing_project:
        return jsonify({"error": "Project ID already exists!"}), 400

    #  Create and add new project to the database
    new_project = Project(project_id=data['project_id'], description=data['description'])
    db.session.add(new_project)
    db.session.commit()

    return jsonify({"message": "Project added successfully!", "project_id": data['project_id']}), 201


@app.route('/api/project_details/<string:project_id>', methods=['GET'])
def get_project_details(project_id):
    """Fetch project details including tasks, subtasks, milestones, and assigned employees."""
    assignments = Assignment.query.filter_by(project_id=project_id).all()

    employees = [
        {"id": emp.id, "name": emp.name, "skills": emp.skills.split(",")}
        for emp in {db.session.get(Employee, a.employee_id) for a in assignments if db.session.get(Employee, a.employee_id)}
    ]

    tasks = []
    for task in Task.query.filter_by(project_id=project_id).all():
        task_data = {"id": task.id, "name": task.name, "subtasks": []}
        
        for subtask in Subtask.query.filter_by(task_id=task.id).all():
            assigned_employee = Assignment.query.filter_by(subtask_id=subtask.id).first()
            employee_info = {
                "id": assigned_employee.employee_id,
                "name": db.session.get(Employee, assigned_employee.employee_id).name
            } if assigned_employee else None

            milestones = [
                {"id": m.id, "name": m.milestone_name, "status": m.status}
                for m in Milestone.query.filter_by(subtask_id=subtask.id).all()
            ]

            task_data["subtasks"].append({
                "id": subtask.id,
                "name": subtask.name,
                "employee": employee_info,
                "milestones": milestones
            })

        tasks.append(task_data)

    return jsonify({"employees": employees, "tasks": tasks})

### --------------- 📌 EMPLOYEE APIs --------------- ###
@app.route('/api/employees', methods=['GET'])
def get_all_employees():
    """Fetch all employees."""
    employees = Employee.query.all()
    return jsonify([{"id": emp.id, "name": emp.name} for emp in employees])

@app.route('/api/logs/<int:employee_id>', methods=['GET'])
def get_logs_for_employee(employee_id):
    """Fetch logs related to a specific employee."""
    logs = AssignmentLog.query.filter_by(employee_id=employee_id).all()
    return jsonify([{"timestamp": log.timestamp, "message": log.log_message} for log in logs])


@app.route('/api/employees/<int:employee_id>/projects', methods=['GET'])
def get_employee_projects(employee_id):
    """Fetch projects assigned to an employee."""
    assignments = Assignment.query.filter_by(employee_id=employee_id).all()
    project_list = [
        {"project_id": p.project_id, "description": Project.query.filter_by(project_id=p.project_id).first().description}
        for p in assignments
    ]
    return jsonify(project_list)

@app.route('/api/employees/<int:employee_id>/tasks', methods=['GET'])
def get_employee_tasks(employee_id):
    """Fetch tasks, subtasks, and milestones assigned to an employee."""
    assignments = Assignment.query.filter_by(employee_id=employee_id).all()

    task_data = {}
    for a in assignments:
        if a.subtask_id:
            subtask = db.session.get(Subtask, a.subtask_id)
            if subtask:
                task = db.session.get(Task, subtask.task_id)
                if task:
                    if task.id not in task_data:
                        task_data[task.id] = {"id": task.id, "task_name": task.name, "subtasks": []}

                    milestones = Milestone.query.filter_by(subtask_id=subtask.id).all()
                    milestone_data = [{"milestone_id": m.id, "name": m.milestone_name, "status": m.status} for m in milestones]

                    task_data[task.id]["subtasks"].append({
                        "subtask_id": subtask.id,
                        "subtask_name": subtask.name,
                        "milestones": milestone_data
                    })

    return jsonify(list(task_data.values()))

### --------------- 📌 AUTOMATIC SUBTASK ASSIGNMENT API --------------- ###

@app.route('/api/assignment_logs/<int:employee_id>', methods=['GET'])
def get_assignment_logs(employee_id):
    """Fetch logs related to task assignment for a specific employee."""
    logs = AssignmentLog.query.filter_by(employee_id=employee_id).order_by(AssignmentLog.timestamp.desc()).all()

    log_data = [{"timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "message": log.log_message} for log in logs]

    return jsonify({"logs": log_data})


@app.route('/api/milestone_complete/<int:milestone_id>', methods=['POST'])
def mark_milestone_complete(milestone_id):
    """Mark a milestone as completed and trigger AI to assign the next subtask."""
    milestone = Milestone.query.get(milestone_id)
    if not milestone:
        return jsonify({"error": "Milestone not found"}), 404

    milestone.status = 1
    milestone.completed_at = datetime.utcnow()
    db.session.commit()

    subtask = Subtask.query.get(milestone.subtask_id)
    if subtask:
        all_milestones = Milestone.query.filter_by(subtask_id=subtask.id).all()
        completed_milestones = [m for m in all_milestones if m.status == 1]

        if len(completed_milestones) == len(all_milestones):
            subtask.status = 1
            db.session.commit()

            print(f" Subtask '{subtask.name}' completed by Employee {milestone.employee_id}!")

            #  AI assigns the next subtask dynamically
            ai_task_agent.assign_next_subtask(milestone.employee_id)

    return jsonify({"message": "Milestone marked as completed!"})

### --------------- 📌 BACKGROUND TASK ASSIGNMENT --------------- ###

def start_task_assignment_thread():
    """Start the background thread inside Flask context."""
    with app.app_context():
        task_thread = threading.Thread(target=assign_tasks_periodically, daemon=True)
        task_thread.start()

def assign_tasks_periodically():
    """Runs AI-based task assignment every 5 minutes."""
    while True:
        with app.app_context():
            print("🔄 Running AI Task Assignment Periodically...")
            ai_task_agent.assign_tasks()
        time.sleep(300)

#  Run Flask App
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    start_task_assignment_thread()
    app.run(debug=True)
