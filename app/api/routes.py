from app.data import repository
from flask import Flask, jsonify, request
from app.service.dashboard_service import DashboardService
from app.data.repository import DashboardRepository

app = Flask(__name__)
repository = DashboardRepository()
service = DashboardService(repository)

@app.route('/dashboard', methods=['GET'])
def get_dashboard():
    data = service.get_dashboard_data()
    return jsonify([{'id': item.id, 'name': item.name, 'value': item.value} for item in data])