import threading
import time
from flask import Flask, render_template, request, jsonify
from database.db import db
from flask_migrate import Migrate
from config import Config
from ai.task_generator import generate_tasks_from_description
from ai.task_assigner import assign_tasks_to_employees  
from ai.task_assigner import assign_next_subtask_to_employee  # ✅ Add this import
from datetime import datetime

# ✅ Initialize Flask App
app = Flask(__name__)
app.config.from_object(Config)

# ✅ Initialize Database
db.init_app(app)
migrate = Migrate(app, db)

# ✅ Import Models AFTER db.init_app(app) to prevent circular imports
from models.employee import Employee
from models.project import Project
from models.task import Task, Milestone
from models.assignment import Assignment
from models.task import Subtask  # ✅ Added for marking subtasks completed

# ✅ Ensure Flask app context is used properly
with app.app_context():
    db.create_all()

### --------------- 📌 PROJECT MANAGER APIs --------------- ###

@app.route('/api/generate_tasks/<string:project_id>', methods=['GET', 'POST'])
def generate_tasks(project_id):
    result = generate_tasks_from_description(project_id)
    return jsonify(result)

@app.route('/api/assign_tasks', methods=['GET', 'POST'])
def assign_tasks():
    result = assign_tasks_to_employees()
    return jsonify(result)

@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([{"project_id": p.project_id, "description": p.description} for p in projects])

@app.route('/api/projects', methods=['POST'])
def add_project():
    data = request.json
    new_project = Project(project_id=data['project_id'], description=data['description'])
    db.session.add(new_project)
    db.session.commit()
    return jsonify({"message": "Project added successfully!"}), 201

### --------------- 📌 EMPLOYEE APIs --------------- ###

@app.route('/api/employees/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    """Get employee details including name and skills."""
    employee = Employee.query.get(employee_id)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify({"id": employee.id, "name": employee.name, "skills": employee.skills.split(",")})

@app.route('/api/employees/<int:employee_id>/add_skill', methods=['POST'])
def add_skill(employee_id):
    """Allow employees to add new skills."""
    data = request.json
    employee = Employee.query.get(employee_id)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    employee.skills += f",{data['skill']}"
    db.session.commit()
    return jsonify({"message": "Skill added successfully!"})

@app.route('/api/employees/<int:employee_id>/projects', methods=['GET'])
def get_employee_projects(employee_id):
    """Fetch projects assigned to an employee."""
    assignments = Assignment.query.filter_by(employee_id=employee_id).all()
    project_list = [{"project_id": p.project_id, "description": Project.query.filter_by(project_id=p.project_id).first().description} for p in assignments]
    return jsonify(project_list)

@app.route('/api/employees/<int:employee_id>/tasks/<string:project_id>', methods=['GET'])
def get_employee_tasks(employee_id, project_id):
    """Fetch tasks, subtasks, and milestones assigned to an employee within a specific project."""
    assignments = Assignment.query.filter_by(employee_id=employee_id, project_id=project_id).all()

    task_data = {}
    
    for a in assignments:
        if a.subtask_id:
            subtask = db.session.get(Subtask, a.subtask_id)
            if subtask:
                task = db.session.get(Task, subtask.task_id)  # Get parent task
                if task:
                    if task.id not in task_data:
                        task_data[task.id] = {
                            "id": task.id,
                            "task_name": task.name,
                            "subtasks": []
                        }

                    # ✅ Fetch milestones for this subtask
                    milestones = Milestone.query.filter_by(subtask_id=subtask.id).all()
                    milestone_data = [{"milestone_id": m.id, "name": m.milestone_name, "status": m.status} for m in milestones]

                    # ✅ Append subtask with its milestones
                    task_data[task.id]["subtasks"].append({
                        "subtask_id": subtask.id,
                        "subtask_name": subtask.name,
                        "milestones": milestone_data
                    })

    return jsonify(list(task_data.values()))



@app.route('/api/employees/<int:employee_id>/complete_task/<int:task_id>', methods=['POST'])
def complete_task(employee_id, task_id):
    """Mark a task as completed, updating assignments & subtasks."""
    assignment = Assignment.query.filter_by(task_id=task_id, employee_id=employee_id).first()
    if assignment:
        assignment.status = 1  # Mark task as completed

        # ✅ Update Subtask
        subtask = Subtask.query.filter_by(task_id=task_id, employee_id=employee_id).first()
        if subtask:
            subtask.status = 1  # Mark as completed

        db.session.commit()
        return jsonify({"message": "Task marked as completed!"})

    return jsonify({"error": "Task not found or not assigned to this employee"}), 404

@app.route('/api/project_details/<string:project_id>', methods=['GET'])
def get_project_details(project_id):
    """Fetch project details including tasks, subtasks, milestones, and assigned employees."""
    assignments = Assignment.query.filter_by(project_id=project_id).all()

    # Fetch all employees working on the project
    employees = [{
        "id": emp.id,
        "name": emp.name,
        "skills": emp.skills.split(",")
    } for emp in {db.session.get(Employee, a.employee_id) for a in assignments if db.session.get(Employee, a.employee_id)}]

    # Fetch all tasks, subtasks, and milestones
    tasks = []
    for task in Task.query.filter_by(project_id=project_id).all():
        task_data = {
            "id": task.id,
            "name": task.name,
            "subtasks": []
        }

        for subtask in Subtask.query.filter_by(task_id=task.id).all():
            # Find the assigned employee for this subtask
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

    return jsonify({
        "employees": employees,
        "tasks": tasks
    })



### --------------- 📌 WEB PAGES --------------- ###

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/employee_dashboard')
def employee_dashboard():
    return render_template('employees.html')

@app.route('/projects')
def project_list():
    return render_template('projects.html')

@app.route('/employee_tasks/<string:project_id>')
def employee_tasks(project_id):
    return render_template('tasks.html', project_id=project_id)


@app.route('/api/milestone_complete/<int:milestone_id>', methods=['POST'])
def mark_milestone_complete(milestone_id):
    """Mark a milestone as completed, check subtask status, and assign new subtasks dynamically."""
    
    milestone = Milestone.query.get(milestone_id)
    if not milestone:
        return jsonify({"error": "Milestone not found"}), 404

    milestone.status = 1
    milestone.completed_at = datetime.utcnow()  # ✅ Mark milestone as completed
    db.session.commit()

    # ✅ Check if all milestones for the subtask are completed
    subtask = Subtask.query.get(milestone.subtask_id)
    if subtask:
        all_milestones = Milestone.query.filter_by(subtask_id=subtask.id).all()
        completed_milestones = [m for m in all_milestones if m.status == 1]

        if len(completed_milestones) == 5:  # ✅ All 5 milestones completed
            subtask.status = 1  # ✅ Mark subtask as completed
            db.session.commit()

            print(f"✅ Subtask '{subtask.name}' completed by Employee {milestone.employee_id}!")

            # ✅ Assign new subtask to this employee
            assign_next_subtask_to_employee(milestone.employee_id)

    return jsonify({
        "message": "Milestone marked as completed!", 
        "completed_at": milestone.completed_at.strftime("%Y-%m-%d %H:%M:%S")
    })


### --------------- 📌 BACKGROUND TASK ASSIGNMENT --------------- ###

def start_task_assignment_thread():
    """Start the background thread inside Flask context."""
    with app.app_context():
        task_thread = threading.Thread(target=assign_tasks_periodically, daemon=True)
        task_thread.start()

def assign_tasks_periodically():
    """Runs task assignment logic every 5 minutes."""
    while True:
        with app.app_context():
            print("🔄 Assigning tasks to employees...")
            assign_tasks_to_employees()
        time.sleep(300)  # 300 seconds = 5 minutes

# ✅ Start background thread for periodic task assignment
task_thread = threading.Thread(target=assign_tasks_periodically, daemon=True)
# task_thread.start()

# ✅ Run Flask App
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    start_task_assignment_thread()
    app.run(debug=True)
