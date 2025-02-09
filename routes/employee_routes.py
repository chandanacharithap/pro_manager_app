from flask import Blueprint, request, jsonify
from models.employee import Employee
from database.db import db

employee_bp = Blueprint('employee_bp', __name__)

@employee_bp.route('/add', methods=['POST'])
def add_employee():
    data = request.json
    new_employee = Employee(
        employee_id=data.get('employee_id'),
        name=data.get('name'),
        skills=data.get('skills')
    )
    db.session.add(new_employee)
    db.session.commit()
    return jsonify({"message": "Employee added successfully!"}), 201
