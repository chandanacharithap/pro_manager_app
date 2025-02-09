from database.db import db
from models.assignment import Assignment
from models.task import Task, Subtask, Milestone
from models.employee import Employee
import time

def assign_tasks_to_employees():
    """Assign subtasks dynamically based on employee skills."""
    
    # ✅ Fetch all unassigned subtasks that are still pending
    unassigned_subtasks = Subtask.query.filter_by(status=0, employee_id=None).all()

    for subtask in unassigned_subtasks:
        task = db.session.get(Task, subtask.task_id)
        if not task:
            continue  

        possible_employees = Employee.query.all()  
        best_match = None  

        for employee in possible_employees:
            employee_skills = [skill.strip().lower() for skill in employee.skills.split(",")]  
            subtask_name = subtask.name.lower()  

            # ✅ Assign employee if any of their skills match the subtask name
            if any(skill in subtask_name for skill in employee_skills):
                best_match = employee
                break  

        if best_match:
            subtask.employee_id = best_match.id
            subtask.status = 1  # ✅ Mark as Assigned
            db.session.commit()

            assignment = Assignment.query.filter_by(
                employee_id=best_match.id,
                project_id=task.project_id,
                subtask_id=subtask.id
            ).first()

            if not assignment:
                assignment_entry = Assignment(
                    employee_id=best_match.id,
                    project_id=task.project_id,
                    subtask_id=subtask.id,  
                    status=1  
                )
                db.session.add(assignment_entry)
                db.session.commit()

            print(f"✅ Assigned Subtask '{subtask.name}' to {best_match.name} (Employee ID: {best_match.id})")

            assign_milestones_to_employee(subtask.id, best_match.id)

    return {"message": "Subtasks assigned successfully!"}


def find_best_matching_employee(subtask_name):
    """Find the best employee based on subtask matching skills."""
    subtask_name = subtask_name.lower()
    possible_employees = Employee.query.all()

    for employee in possible_employees:
        employee_skills = [skill.strip().lower() for skill in employee.skills.split(",")]

        if any(skill in subtask_name for skill in employee_skills):
            return employee  # ✅ Return the first matching employee

    return None  # No match found


def assign_milestones_to_employee(subtask_id, employee_id):
    """Assign all milestones of a subtask to the same employee working on the subtask."""
    
    milestones = Milestone.query.filter_by(subtask_id=subtask_id, employee_id=None).all()

    for milestone in milestones:
        milestone.employee_id = employee_id
        milestone.status = 0  # ✅ Set as "Not Started"
        db.session.commit()

        print(f"✅ Assigned Milestone '{milestone.milestone_name}' to Employee {employee_id}")


def check_and_update_task_status():
    """Checks if all subtasks of a task are completed and updates the task status."""
    
    all_tasks = Task.query.all()

    for task in all_tasks:
        subtasks = Subtask.query.filter_by(task_id=task.id).all()
        
        if all(subtask.status == 1 for subtask in subtasks):  
            task.status = 1  # ✅ Mark task as Completed
            db.session.commit()
            print(f"✅ Task '{task.name}' is now marked as completed!")

    return {"message": "Task status updated successfully!"}


def assign_next_subtask_to_employee(employee_id):
    """Assign the next available subtask to an employee after they complete their previous one."""
    
    print(f"🔄 Checking for new subtasks for Employee {employee_id}...")

    # ✅ Get the employee details
    employee = Employee.query.get(employee_id)
    if not employee:
        print(f"⚠️ Employee {employee_id} not found!")
        return {"error": "Employee not found."}

    employee_skills = [skill.strip().lower() for skill in employee.skills.split(",")]
    print(f"👨‍💻 Employee {employee.name} has skills: {employee_skills}")

    # ✅ Get available subtasks that are unassigned (status = 0)
    available_subtasks = Subtask.query.filter_by(status=0, employee_id=None).all()
    print(f"🔍 Found {len(available_subtasks)} unassigned subtasks.")

    for subtask in available_subtasks:
        subtask_name = subtask.name.lower()

        # ✅ Assign if at least one of the employee's skills matches the subtask name
        if any(skill in subtask_name for skill in employee_skills):
            print(f"✅ Assigning '{subtask.name}' to {employee.name}...")

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

            print(f"🎯 New Subtask '{subtask.name}' assigned to {employee.name} (Employee ID: {employee.id})")

            # ✅ Assign all milestones to the employee
            assign_milestones_to_employee(subtask.id, employee.id)

            return {"message": f"New subtask '{subtask.name}' assigned to {employee.name}."}

    print(f"⚠️ No suitable subtasks found for Employee {employee_id} with skills {employee_skills}.")
    return {"message": "No matching subtasks available for this employee."}



def assign_tasks_periodically():
    """Periodically assigns subtasks and milestones to employees."""
    
    while True:
        print("🔄 Assigning tasks to employees...")
        assign_tasks_to_employees()
        check_and_update_task_status()

        # ✅ Assign new subtasks to employees who completed their previous one
        completed_employees = Assignment.query.filter_by(status=1).all()
        for assignment in completed_employees:
            assign_next_subtask_to_employee(assignment.employee_id)

        time.sleep(60)  # ✅ Runs every 60 seconds
