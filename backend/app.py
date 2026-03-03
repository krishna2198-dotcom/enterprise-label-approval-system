from flask import Flask, jsonify, request
from flask_cors import CORS
from azure.cosmos import CosmosClient
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

client = CosmosClient(
    os.getenv("COSMOS_ENDPOINT"),
    os.getenv("COSMOS_KEY")
)
database = client.get_database_client(os.getenv("COSMOS_DATABASE"))
container = database.get_container_client(os.getenv("COSMOS_CONTAINER"))

@app.route('/')
def home():
    return jsonify({"message": "Task Manager API Running!"})

@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = list(container.read_all_items())
    return jsonify(tasks)

@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.json
    task = {
        "id": str(uuid.uuid4()),
        "title": data['title'],
        "status": data.get('status', 'pending')
    }
    container.create_item(task)
    return jsonify({"message": "Task added!", "task": task})

@app.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    container.delete_item(item=task_id, partition_key=task_id)
    return jsonify({"message": "Task deleted!"})

@app.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json
    task = container.read_item(item=task_id, partition_key=task_id)
    task['status'] = data.get('status', task['status'])
    task['title'] = data.get('title', task['title'])
    container.replace_item(item=task_id, body=task)
    return jsonify({"message": "Task updated!", "task": task})

if __name__ == '__main__':
    app.run(debug=True)