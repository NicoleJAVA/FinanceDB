from flask import Blueprint, jsonify, request

api_routes = Blueprint('api_routes', __name__)

@api_routes.route('/api/data', methods=['POST'])
def data():
    data = request.json
    return jsonify({"received_data": data})