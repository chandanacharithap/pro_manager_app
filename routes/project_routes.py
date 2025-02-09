from flask import Blueprint, request, jsonify
from models.project import Project
from database.db import db

project_bp = Blueprint('project_bp', __name__)

@project_bp.route('/add', methods=['POST'])
def add_project():
    data = request.json
    new_project = Project(
        project_id=data.get('project_id'),
        description=data.get('description')
    )
    db.session.add(new_project)
    db.session.commit()
    return jsonify({"message": "Project added successfully!"}), 201
