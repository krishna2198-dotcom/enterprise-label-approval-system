from flask import Flask, jsonify, request
from flask_cors import CORS
from azure.cosmos import CosmosClient
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

# ── Model ──────────────────────────────────────────────────────
class Task:
    def __init__(self, title, status="pending", task_id=None):
        self.id = task_id or str(uuid.uuid4())
        self.title = title
        self.status = status

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status
        }

    @staticmethod
    def from_dict(data):
        return Task(
            title=data["title"],
            status=data.get("status", "pending"),
            task_id=data.get("id")
        )


# ── Repository (Data Access Layer) ─────────────────────────────
class TaskRepository:
    def __init__(self):
        client = CosmosClient(
            os.getenv("COSMOS_ENDPOINT"),
            os.getenv("COSMOS_KEY")
        )
        database = client.get_database_client(os.getenv("COSMOS_DATABASE"))
        self.container = database.get_container_client(
            os.getenv("COSMOS_CONTAINER")
        )

    def get_all(self):
        items = list(self.container.read_all_items())
        return [Task.from_dict(item) for item in items]

    def create(self, task: Task):
        self.container.create_item(task.to_dict())
        return task

    def update(self, task_id, data):
        item = self.container.read_item(
            item=task_id, partition_key=task_id
        )
        item["title"] = data.get("title", item["title"])
        item["status"] = data.get("status", item["status"])
        self.container.replace_item(item=task_id, body=item)
        return Task.from_dict(item)

    def delete(self, task_id):
        self.container.delete_item(
            item=task_id, partition_key=task_id
        )


# ── Service (Business Logic Layer) ─────────────────────────────
class TaskService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def get_all_tasks(self):
        return [t.to_dict() for t in self.repository.get_all()]

    def add_task(self, title, status="pending"):
        task = Task(title=title, status=status)
        return self.repository.create(task).to_dict()

    def update_task(self, task_id, data):
        return self.repository.update(task_id, data).to_dict()

    def delete_task(self, task_id):
        self.repository.delete(task_id)


# ── Controller (Flask Routes) ───────────────────────────────────
app = Flask(__name__)
CORS(app)

repo = TaskRepository()
service = TaskService(repo)

@app.route('/')
def home():
    return jsonify({"message": "Task Manager API Running!"})

@app.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(service.get_all_tasks())

@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.json
    task = service.add_task(data['title'], data.get('status', 'pending'))
    return jsonify({"message": "Task added!", "task": task})

@app.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json
    task = service.update_task(task_id, data)
    return jsonify({"message": "Task updated!", "task": task})

@app.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    service.delete_task(task_id)
    return jsonify({"message": "Task deleted!"})

if __name__ == '__main__':
    app.run(debug=True)