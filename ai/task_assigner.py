from database.db import db
from models.assignment import Assignment
from models.task import Task, Subtask, Milestone
from models.employee import Employee
import time
from models.logs import AssignmentLog

def log_assignment(employee_id, message):
    """Store assignment log messages in the database."""
    log_entry = AssignmentLog(employee_id=employee_id, log_message=message)
    db.session.add(log_entry)
    db.session.commit()
    print(f"📝 Log stored: {message}")



# AI Task Assignment Agent
class AITaskAssignmentAgent:
    def __init__(self, max_capacity=1):
        self.max_capacity = max_capacity  # Max subtasks an employee can handle at once

    def assign_tasks(self):
        """Assign subtasks dynamically using AI logic based on employee skills."""
        
        available_employees = Employee.query.all()

        for employee in available_employees:
            # ✅ Check if employee is already working on a subtask
            active_assignment = Assignment.query.filter_by(employee_id=employee.id, status=1).first()

            if active_assignment:
                print(f"⏳ Employee {employee.id} is still working on a task. Waiting for completion.")
                continue  # ✅ Skip assigning a new subtask until current one is completed

            # ✅ Find the best matching subtask for this employee
            matching_subtask = self.find_best_matching_subtask(employee)

            if not matching_subtask:
                print(f"⚠️ No matching subtasks found for Employee {employee.id}.")
                continue  

            # ✅ Get the project ID from the associated Task
            project = db.session.get(Task, matching_subtask.task_id)
            project_id = project.project_id if project else None

            if not project_id:
                print(f"⚠️ Could not find a project for subtask {matching_subtask.id}. Skipping.")
                continue  # Skip this subtask if no project is found

            # ✅ Assign the subtask to the employee
            matching_subtask.employee_id = employee.id
            matching_subtask.status = 1  # ✅ Mark as Assigned
            db.session.commit()

            # ✅ Create an assignment record
            assignment_entry = Assignment(
                employee_id=employee.id,
                project_id=project_id,  # ✅ Correct project_id
                subtask_id=matching_subtask.id,
                status=1  # ✅ Task in Progress
            )
            db.session.add(assignment_entry)
            db.session.commit()

            print(f"✅ Assigned Subtask '{matching_subtask.name}' to {employee.name} (Employee ID: {employee.id})")

            # ✅ Assign milestones **only after subtask assignment**
            self.assign_milestones_to_employee(matching_subtask.id, employee.id)

        return {"message": "Subtasks assigned successfully!"}

    def find_best_matching_subtask(self, employee):
        """Find the best available subtask for an employee based on skills."""
        
        employee_skills = set(skill.strip().lower() for skill in employee.skills.split(","))  # ✅ Normalize skills
        available_subtasks = Subtask.query.filter_by(status=0, employee_id=None).all()  # ✅ Fetch all unassigned subtasks

        best_match = None
        highest_match_score = 0

        for subtask in available_subtasks:
            subtask_words = set(subtask.name.lower().split())  # ✅ Split subtask name into words

            # ✅ Calculate match score: Count how many skill words appear in the subtask name
            match_score = sum(1 for skill in employee_skills if skill in subtask_words or any(word in skill for word in subtask_words))

            # ✅ Select the subtask with the highest match score
            if match_score > highest_match_score:
                best_match = subtask
                highest_match_score = match_score
        print(f"🔍 Checking available subtasks for Employee {employee.id} ({employee.name}):")
        for subtask in available_subtasks:
            print(f"📌 Subtask: {subtask.name}")

        if best_match:
            print(f"✅ Best match for {employee.name}: {best_match.name}")
        else:
            print(f"⚠️ No suitable subtask found for Employee {employee.name}")

        return best_match  # ✅ Return the best-matching subtask


    def assign_milestones_to_employee(self, subtask_id, employee_id):
        """Assign all milestones of a subtask to the same employee working on the subtask."""
        milestones = Milestone.query.filter_by(subtask_id=subtask_id, employee_id=None).all()

        for milestone in milestones:
            milestone.employee_id = employee_id
            milestone.status = 0  # ✅ Set as "Not Started"
            db.session.commit()

            print(f"✅ Assigned Milestone '{milestone.milestone_name}' to Employee {employee_id}")

    def check_and_update_task_status(self):
        """Checks if all subtasks of a task are completed and updates the task status."""
        all_tasks = Task.query.all()

        for task in all_tasks:
            subtasks = Subtask.query.filter_by(task_id=task.id).all()

            if all(subtask.status == 1 for subtask in subtasks):  
                task.status = 1  # ✅ Mark task as Completed
                db.session.commit()
                print(f"✅ Task '{task.name}' is now marked as completed!")

        return {"message": "Task status updated successfully!"}
    

    def assign_next_subtask(self, employee_id):
        """Assign the next available subtask only after the employee completes the current one."""
        
        print(f"🔄 Checking for new subtasks for Employee {employee_id}...")

        employee = Employee.query.get(employee_id)
        if not employee:
            log_assignment(employee_id, f"⚠️ Employee {employee_id} not found!")
            return {"error": "Employee not found."}

        employee_skills = [skill.strip().lower() for skill in employee.skills.split(",")]
        log_assignment(employee_id, f"👨‍💻 Employee {employee.name} has skills: {employee_skills}")

        available_subtasks = Subtask.query.filter_by(status=0, employee_id=None).all()
        log_assignment(employee_id, f"🔍 Found {len(available_subtasks)} unassigned subtasks.")

        for subtask in available_subtasks:
            subtask_name = subtask.name.lower()

            if any(skill in subtask_name for skill in employee_skills):
                subtask.employee_id = employee.id
                subtask.status = 1  # ✅ Mark as Assigned
                db.session.commit()

                task = db.session.get(Task, subtask.task_id)

                assignment_entry = Assignment(
                    employee_id=employee.id,
                    project_id=task.project_id,
                    subtask_id=subtask.id,
                    status=1  
                )
                db.session.add(assignment_entry)
                db.session.commit()

                log_assignment(employee_id, f"✅ Assigned Subtask '{subtask.name}' to {employee.name} (Employee ID: {employee.id})")

                # ✅ Assign all milestones only after subtask assignment
                self.assign_milestones_to_employee(subtask.id, employee.id)

                return {"message": f"New subtask '{subtask.name}' assigned to {employee.name}."}

        log_assignment(employee_id, f"⚠️ No suitable subtasks found for Employee {employee_id} with skills {employee_skills}.")
        return {"message": "No matching subtasks available for this employee."}

    
# ✅ AI Agent Instance
ai_task_agent = AITaskAssignmentAgent()

def assign_tasks_periodically():
    """Periodically assigns subtasks and milestones to employees using AI logic."""
    
    while True:
        print("🔄 Assigning tasks using AI agent...")
        ai_task_agent.assign_tasks()
        ai_task_agent.check_and_update_task_status()

        # ✅ Assign new subtasks to employees who completed their previous one
        completed_employees = Assignment.query.filter_by(status=1).all()
        for assignment in completed_employees:
            ai_task_agent.assign_next_subtask_to_employee(assignment.employee_id)

        time.sleep(60)  # ✅ Runs every 60 seconds
