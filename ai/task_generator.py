import openai
import re
from database.db import db
from models.project import Project
from models.task import Task, Subtask, Milestone
from config import Config
from ai.task_assigner import ai_task_agent  # Use AI agent for assignment

#  Initialize OpenAI Client
client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)

def generate_tasks_from_description(project_id):
    """Uses OpenAI GPT-3.5 to analyze project description and generate structured tasks, subtasks, and milestones."""
    
    #  Fetch Project Details
    project = Project.query.filter_by(project_id=project_id).first()
    if not project:
        return {"error": "Project not found"}, 404  

    description = project.description
    
    #  AI Prompt
    prompt = f"""
You are an AI-powered project manager. Given a detailed project description, generate **realistic tasks, subtasks, and milestones** needed to complete the project.

### **Rules for Task Generation:**
- **List tasks as categories** (e.g., Backend, Frontend, Machine Learning, etc.).
- **Each task must have at least 2-3 specific subtasks**.
- **Each subtask must be broken down into **exactly 5 milestones**.
- **Milestones should represent small, clear steps towards completing a subtask**.
- **Do NOT include unnecessary text, just output the structured breakdown.**

---

### **Project Description**:
{description}

### **Expected Output Format**:
**Backend Development**
- Develop API endpoints for authentication
    - Setup API structure
    - Implement user authentication endpoint
    - Secure API using JWT
    - Implement API testing
    - Deploy API to production

- Implement database schema
    - Design tables and relationships
    - Create migration scripts
    - Implement indexing for performance
    - Seed initial data
    - Perform database testing

Now, generate the structured task breakdown for this project:
"""

    try:
        #  Generate AI Response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )

        tasks_text = response.choices[0].message.content.strip()

        # Debugging: Print AI response
        print(f"🔍 AI Response:\n{tasks_text}")

        current_task = None  
        current_subtask = None  
        milestones = []
        subtask_list = []  # Keep track of all created subtasks

        for line in tasks_text.split("\n"):
            print(f"🔍 Processing Line: {line}")

            task_match = re.match(r"^\*\*(.*?)\*\*", line)  
            subtask_match = re.match(r"^- (.+)", line)  
            milestone_match = re.match(r"^\s+- (.+)", line)  

            if task_match:
                task_name = task_match.group(1).strip()
                print(f"Task Detected: {task_name}")  

                current_task = Task(name=task_name[:255], project_id=project_id, status=0)
                db.session.add(current_task)
                db.session.commit()  

            elif subtask_match and current_task:
                subtask_name = subtask_match.group(1).strip()
                print(f" Subtask Detected: {subtask_name}")  

                current_subtask = Subtask(
                    name=subtask_name[:255], 
                    task_id=current_task.id,  
                    status=0  
                )
                db.session.add(current_subtask)
                db.session.commit()
                subtask_list.append(current_subtask)  #  Store for later assignment
                milestones = []  

            elif milestone_match and current_subtask:
                milestone_name = milestone_match.group(1).strip()
                if len(milestones) < 5:  
                    print(f" Milestone Detected: {milestone_name}")  
                    milestone_entry = Milestone(
                        milestone_name=milestone_name[:255], 
                        subtask_id=current_subtask.id,
                        employee_id=None,  
                        status=0  
                    )
                    db.session.add(milestone_entry)
                    milestones.append(milestone_entry)

        db.session.commit()

        #  Assign only **ONE subtask per employee initially**
        ai_task_agent.assign_tasks()

        return {"message": " Tasks, Subtasks, and Milestones generated and assigned successfully!"}

    except openai.OpenAIError as e:  
        db.session.rollback()
        return {"error": f"OpenAI API error: {str(e)}"}, 500
    except Exception as e:
        db.session.rollback()
        return {"error": f"Unexpected error: {str(e)}"}, 500
