// Fetch Employee Skills
function fetchSkills() {
    fetch('/api/employee/skills')
    .then(response => response.json())
    .then(data => {
        let skillList = document.getElementById("skill-list");
        skillList.innerHTML = ""; // Clear list before updating
        data.skills.forEach(skill => {
            let li = document.createElement("li");
            li.textContent = skill;
            skillList.appendChild(li);
        });
    })
    .catch(error => console.error("Error fetching skills:", error));
}

// Add a New Skill
function addSkill() {
    let newSkill = document.getElementById("new-skill").value;
    if (newSkill.trim() === "") {
        alert("Skill cannot be empty!");
        return;
    }

    fetch('/api/employee/skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill: newSkill })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        fetchSkills(); // Refresh the skill list
    })
    .catch(error => console.error("Error adding skill:", error));
}

// Fetch Assigned Projects
function fetchAssignedProjects() {
    fetch('/api/employee/projects')
    .then(response => response.json())
    .then(data => {
        let projectList = document.getElementById("assigned-projects");
        projectList.innerHTML = "";
        data.projects.forEach(project => {
            let li = document.createElement("li");
            li.textContent = `${project.project_id} - ${project.description}`;
            projectList.appendChild(li);
        });
    })
    .catch(error => console.error("Error fetching assigned projects:", error));
}

// Load data when page loads
document.addEventListener("DOMContentLoaded", function() {
    fetchSkills();
    fetchAssignedProjects();
});


// Fetch Projects from API
function fetchProjects() {
    fetch('/api/projects')
    .then(response => response.json())
    .then(data => {
        let list = document.getElementById("project-list");
        list.innerHTML = ""; // Clear previous data
        data.forEach(proj => {
            let li = document.createElement("li");
            li.textContent = `${proj.project_id} - ${proj.description}`;
            list.appendChild(li);
        });
    })
    .catch(error => console.error("Error fetching projects:", error));
}


// Handle Form Submission to Add a New Project
document.getElementById("project-form").addEventListener("submit", function(event) {
    event.preventDefault();

    let projectData = {
        project_id: document.getElementById("project_id").value,
        description: document.getElementById("description").value
    };

    fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(projectData)
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("message").textContent = data.message;
        fetchProjects();  // Refresh the project list
    })
    .catch(error => console.error("Error:", error));
});

document.addEventListener("DOMContentLoaded", function() {
    let employeeId = 1;  // Assume logged-in employee has ID 1

    // Fetch Employee Skills
    fetch(`/api/skills/${employeeId}`)
    .then(response => response.json())
    .then(data => {
        let skillsList = document.getElementById("skills-list");
        skillsList.innerHTML = "";  
        data.skills.forEach(skill => {
            let li = document.createElement("li");
            li.textContent = skill;
            skillsList.appendChild(li);
        });
    });

    // Add New Skill
    document.getElementById("add-skill-form")?.addEventListener("submit", function(event) {
        event.preventDefault();
        let skill = document.getElementById("new-skill").value;

        fetch('/api/add_skill', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ skill: skill })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            location.reload();
        });
    });

    // Fetch Employee Projects
    fetch(`/api/projects/${employeeId}`)
    .then(response => response.json())
    .then(data => {
        let projectsList = document.getElementById("projects-list");
        projectsList.innerHTML = "";  
        data.forEach(project => {
            let li = document.createElement("li");
            let link = document.createElement("a");
            link.href = `/employee_tasks/${project.project_id}`;
            link.textContent = project.description;
            li.appendChild(link);
            projectsList.appendChild(li);
        });
    });

    // Fetch Tasks in a Project
    let projectId = window.location.pathname.split("/").pop(); // Get project_id from URL
    fetch(`/api/tasks/${projectId}/${employeeId}`)
    .then(response => response.json())
    .then(data => {
        let tasksList = document.getElementById("tasks-list");
        tasksList.innerHTML = "";  
        data.forEach(task => {
            let li = document.createElement("li");
            li.innerHTML = `${task.name} <button onclick="markTaskCompleted(${task.id})">Complete</button>`;
            tasksList.appendChild(li);
        });
    });
});

// Mark Task as Completed
function markTaskCompleted(taskId) {
    fetch(`/api/complete_task/${taskId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        location.reload();
    });
}
