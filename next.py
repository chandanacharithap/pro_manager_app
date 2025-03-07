<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Employee Dashboard</title>
    <style>
        /* General Styling */
        body {
            font-family: Arial, sans-serif;
            background-color: #f8f9fa;
            margin: 0;
            padding: 20px;
        }
        h1, h2 {
            text-align: center;
            color: #007bff;
        }
        .container {
            max-width: 800px;
            margin: auto;
        }
        .box {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        h2 {
            border-bottom: 2px solid #007bff;
            padding-bottom: 5px;
            color: #007bff;
        }
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            background: #fff;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
        }
        .task-title {
            font-weight: bold;
        }
        .subtask-title {
            font-style: italic;
            padding-left: 15px;
            font-weight: bold;
        }
        /* Progress Bar */
        .subtask-progress {
            width: 100%;
            height: 12px;
            background: #ddd;
            border-radius: 6px;
            overflow: hidden;
            margin: 10px 0;
            position: relative;
        }
        .progress-bar {
            height: 100%;
            background: #28a745;
            width: 0%;
            transition: width 0.5s ease-in-out;
            position: relative;
        }
        /* Tooltip */
        .tooltip {
            position: absolute;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            background: black;
            color: white;
            padding: 3px 6px;
            font-size: 12px;
            border-radius: 4px;
            display: none;
        }
        .subtask-progress:hover .tooltip {
            display: block;
        }
        .milestone-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .completed {
            text-decoration: line-through;
            color: green;
            font-style: italic;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        button:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>

    <div class="container">
        <h1>Employee Dashboard</h1>

        <!-- Employee ID Input -->
        <div class="box">
            <label for="employee-id">Enter Your Employee ID:</label>
            <input type="number" id="employee-id" placeholder="Employee ID" required>
            <button onclick="fetchEmployeeSkills()">Get Skills</button>
            <button onclick="fetchEmployeeProjects()">Get Projects</button>
            <button onclick="fetchEmployeeTasks()">Get Tasks</button>
        </div>

        <!-- Employee Skills -->
        <div class="box">
            <h2>Your Skills</h2>
            <ul id="skills-list"></ul>
        </div>

        <!-- Assigned Projects -->
        <div class="box">
            <h2>Your Assigned Projects</h2>
            <ul id="projects-list"></ul>
        </div>

        <!-- Assigned Tasks -->
        <div class="box">
            <h2>Your Assigned Tasks</h2>
            <div id="assigned-tasks"></div>
        </div>
    </div>

    <script>
        function getEmployeeId() {
            return document.getElementById("employee-id").value || 5;
        }

        function fetchEmployeeSkills() {
            let employeeId = getEmployeeId();
            fetch(`/api/employees/${employeeId}`)
                .then(response => response.json())
                .then(data => {
                    let skillsList = document.getElementById("skills-list");
                    skillsList.innerHTML = "";
                    data.skills.forEach(skill => {
                        let li = document.createElement("li");
                        li.textContent = skill;
                        skillsList.appendChild(li);
                    });
                })
                .catch(error => console.error("Error fetching skills:", error));
        }

        function fetchEmployeeProjects() {
            let employeeId = getEmployeeId();
            fetch(`/api/employees/${employeeId}/projects`)
                .then(response => response.json())
                .then(data => {
                    let projectsList = document.getElementById("projects-list");
                    projectsList.innerHTML = "";
                    data.forEach(project => {
                        let li = document.createElement("li");
                        li.textContent = `${project.project_id}: ${project.description}`;
                        projectsList.appendChild(li);
                    });
                })
                .catch(error => console.error("Error fetching projects:", error));
        }

        function fetchEmployeeTasks() {
            let employeeId = getEmployeeId();
            let projectId = "P006"; 

            fetch(`/api/employees/${employeeId}/tasks/${projectId}`)
                .then(response => response.json())
                .then(tasks => {
                    let tasksContainer = document.getElementById("assigned-tasks");
                    tasksContainer.innerHTML = "";

                    tasks.forEach(task => {
                        let taskDiv = document.createElement("div");
                        taskDiv.className = "box";
                        taskDiv.innerHTML = `<div class="task-title">${task.task_name}</div>`;

                        task.subtasks.forEach(subtask => {
                            let subtaskDiv = document.createElement("div");
                            subtaskDiv.className = "subtask-title";
                            subtaskDiv.textContent = subtask.subtask_name;
                            taskDiv.appendChild(subtaskDiv);

                            let progressContainer = document.createElement("div");
                            progressContainer.className = "subtask-progress";

                            let progressBar = document.createElement("div");
                            progressBar.className = "progress-bar";
                            let completedMilestones = subtask.milestones.filter(m => m.status === 1).length;
                            let progress = (completedMilestones / 5) * 100; 
                            progressBar.style.width = `${progress}%`;

                            let tooltip = document.createElement("div");
                            tooltip.className = "tooltip";
                            tooltip.textContent = `${progress}%`;
                            progressBar.appendChild(tooltip);

                            progressContainer.appendChild(progressBar);
                            taskDiv.appendChild(progressContainer);
                            
                            task.subtasks.forEach(subtask => {
                            let subtaskDiv = document.createElement("div");
                            subtaskDiv.className = "subtask-title";
                            subtaskDiv.textContent = subtask.subtask_name;

                            if (subtask.completed) {
                                let newTaskButton = document.createElement("button");
                                newTaskButton.textContent = "Ready for New Task";
                                newTaskButton.style.marginLeft = "10px";
                                newTaskButton.onclick = () => assignNextTask(employeeId);

                                subtaskDiv.appendChild(newTaskButton);
                            }

                            taskDiv.appendChild(subtaskDiv);
                        });

                            subtask.milestones.forEach(milestone => {
                                let milestoneDiv = document.createElement("div");
                                milestoneDiv.className = "milestone-container";

                                let milestoneText = document.createElement("span");
                                milestoneText.textContent = milestone.name;

                                let completeButton = document.createElement("button");
                                completeButton.textContent = "Mark as Completed";
                                completeButton.onclick = () => markMilestoneCompleted(milestone.milestone_id, progressBar, tooltip, milestoneText);

                                milestoneDiv.appendChild(milestoneText);
                                milestoneDiv.appendChild(completeButton);
                                taskDiv.appendChild(milestoneDiv);
                            });

                            tasksContainer.appendChild(taskDiv);
                        });
                    });
                })
                .catch(error => console.error("Error fetching tasks:", error));
        }

        function markMilestoneCompleted(milestoneId, progressBar, tooltip, milestoneText) {
            fetch(`/api/milestone_complete/${milestoneId}`, { method: "POST" })
                .then(response => response.json())
                .then(data => {
                    milestoneText.classList.add("completed");
                    milestoneText.innerHTML += ` <small>(Completed on: ${new Date(data.completed_at).toLocaleString()})</small>`;

                    let currentProgress = parseInt(progressBar.style.width) || 0;
                    let newProgress = currentProgress + 20;  // Each milestone adds 20%
                    if (newProgress > 100) newProgress = 100;

                    progressBar.style.width = `${newProgress}%`;
                    tooltip.textContent = `${newProgress}%`;
                })
                .catch(error => console.error("Error updating milestone:", error));
        }

        function assignNextTask(employeeId) {
            fetch(`/api/assign_next_task/${employeeId}`, { method: "POST" })
                .then(response => response.json())
                .then(data => {
                    alert(`You have been assigned a new task: ${data.task_name}`);
                    fetchEmployeeTasks();
                })
                .catch(error => console.error("Error assigning new task:", error));
        }
    </script>

</body>
</html>
