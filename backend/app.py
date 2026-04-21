from flask import Flask, jsonify, request, session, redirect
from flask_cors import CORS
from azure.cosmos import CosmosClient
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import requests as req

load_dotenv()

# ── In-memory user store (replaces session for local dev) ────────
user_store = {}

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY"),
    SESSION_COOKIE_SAMESITE=None,
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=False,
)
CORS(app,
     supports_credentials=True,
     origins=["http://localhost:3000"],
     allow_headers=["Content-Type", "Authorization", "X-Auth-Token"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# ── CosmosDB Setup ──────────────────────────────────────────────
client = CosmosClient(
    os.getenv("COSMOS_ENDPOINT"),
    os.getenv("COSMOS_KEY")
)
database = client.get_database_client(os.getenv("COSMOS_DATABASE"))
labels_container = database.get_container_client("labels")
audit_container = database.get_container_client("audit_logs")


# ── Auth Helpers ─────────────────────────────────────────────────
def get_current_user():
    token = request.headers.get('X-Auth-Token') or request.args.get('token')
    if token and token in user_store:
        return user_store[token]
    return None

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Auth-Token')
        if not token or token not in user_store:
            return jsonify({
                "error": "Not authenticated",
                "login_url": "/auth/login"
            }), 401
        return f(*args, **kwargs)
    return decorated


# ── Model ───────────────────────────────────────────────────────
class Label:
    def __init__(self, product_name, label_type,
                 submitted_by, content, label_id=None):
        self.id = label_id or str(uuid.uuid4())
        self.product_name = product_name
        self.label_type = label_type
        self.submitted_by = submitted_by
        self.content = content
        self.status = "Draft"
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "product_name": self.product_name,
            "label_type": self.label_type,
            "submitted_by": self.submitted_by,
            "content": self.content,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @staticmethod
    def from_dict(data):
        return data


# ── Audit Logger ────────────────────────────────────────────────
class AuditLogger:
    def __init__(self, container):
        self.container = container

    def log(self, label_id, action, performed_by, details=""):
        log_entry = {
            "id": str(uuid.uuid4()),
            "label_id": label_id,
            "action": action,
            "performed_by": performed_by,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.container.create_item(log_entry)
        return log_entry


# ── Validator (IQ/OQ/PQ simulation) ─────────────────────────────
class LabelValidator:
    REQUIRED_FIELDS = [
        "product_name", "label_type",
        "submitted_by", "content"
    ]
    VALID_LABEL_TYPES = [
        "Primary", "Secondary", "Insert", "Carton"
    ]

    def validate(self, data):
        errors = []
        for field in self.REQUIRED_FIELDS:
            if not data.get(field):
                errors.append(f"{field} is required")
        if data.get("label_type") not in self.VALID_LABEL_TYPES:
            errors.append(
                f"label_type must be one of "
                f"{self.VALID_LABEL_TYPES}"
            )
        return errors


# ── Repository ──────────────────────────────────────────────────
class LabelRepository:
    def __init__(self, container):
        self.container = container

    def get_all(self):
        return list(self.container.read_all_items())

    def get_by_id(self, label_id):
        return self.container.read_item(
            item=label_id, partition_key=label_id
        )

    def create(self, label_dict):
        return self.container.create_item(label_dict)

    def update_status(self, label_id, new_status):
        item = self.get_by_id(label_id)
        item["status"] = new_status
        item["updated_at"] = datetime.utcnow().isoformat()
        return self.container.replace_item(
            item=label_id, body=item
        )


# ── Email Notifier (SendGrid SaaS) ──────────────────────────────
class EmailNotifier:
    def __init__(self):
        self.client = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        self.sender = os.getenv("SENDER_EMAIL")
        self.notify_email = os.getenv("NOTIFY_EMAIL")

    def send_notification(self, label, new_status):
        try:
            subject = f"Label Update: {label['product_name']} → {new_status}"
            body = f"""
            <h2>Pharma Label Workflow Update</h2>
            <p>A label has been updated in the system.</p>
            <table border="1" cellpadding="8" cellspacing="0">
                <tr><td><b>Product</b></td><td>{label['product_name']}</td></tr>
                <tr><td><b>Label Type</b></td><td>{label['label_type']}</td></tr>
                <tr><td><b>New Status</b></td><td>{new_status}</td></tr>
                <tr><td><b>Updated At</b></td><td>{datetime.utcnow().isoformat()}</td></tr>
            </table>
            <p>Please log in to the system to take action.</p>
            <br>
            <small>This is an automated notification from Pharma Workflow System</small>
            """
            message = Mail(
                from_email=self.sender,
                to_emails=self.notify_email,
                subject=subject,
                html_content=body
            )
            self.client.send(message)
            return True
        except Exception as e:
            print(f"Email notification failed: {e}")
            return False

    def send_approval_email(self, label, sap_result):
        try:
            subject = f"APPROVED: {label['product_name']} — SAP Material Generated"
            body = f"""
            <h2 style="color: green;">Label Approved & Posted to SAP</h2>
            <p>The following label has been approved and posted to SAP.</p>
            <table border="1" cellpadding="8" cellspacing="0">
                <tr><td><b>Product</b></td><td>{label['product_name']}</td></tr>
                <tr><td><b>Label Type</b></td><td>{label['label_type']}</td></tr>
                <tr><td><b>SAP Material Number</b></td><td>{sap_result['sap_material_number']}</td></tr>
                <tr><td><b>SAP Status</b></td><td>{sap_result['sap_status']}</td></tr>
                <tr><td><b>Approved At</b></td><td>{sap_result['approved_at']}</td></tr>
            </table>
            <p style="color: green;"><b>This label is now cleared for manufacturing.</b></p>
            <br>
            <small>This is an automated notification from Pharma Workflow System</small>
            """
            message = Mail(
                from_email=self.sender,
                to_emails=self.notify_email,
                subject=subject,
                html_content=body
            )
            self.client.send(message)
            return True
        except Exception as e:
            print(f"Approval email failed: {e}")
            return False


# ── SAP Integration Simulation ───────────────────────────────────
class SAPIntegration:
    def send_to_sap(self, label):
        sap_payload = {
            "sap_material_number": f"MAT-{label['id'][:8].upper()}",
            "product_name": label["product_name"],
            "label_type": label["label_type"],
            "approval_status": "APPROVED",
            "approved_at": datetime.utcnow().isoformat(),
            "sap_status": "POSTED"
        }
        return sap_payload


# ── Service ─────────────────────────────────────────────────────
class LabelService:
    def __init__(self, repo, auditor, validator, sap, notifier):
        self.repo = repo
        self.auditor = auditor
        self.validator = validator
        self.sap = sap
        self.notifier = notifier

    def get_all_labels(self):
        return self.repo.get_all()

    def submit_label(self, data):
        errors = self.validator.validate(data)
        if errors:
            return None, errors

        label = Label(
            product_name=data["product_name"],
            label_type=data["label_type"],
            submitted_by=data["submitted_by"],
            content=data["content"]
        )
        label_dict = label.to_dict()
        self.repo.create(label_dict)
        self.auditor.log(
            label.id, "CREATED",
            data["submitted_by"],
            "Label submitted for review"
        )
        self.notifier.send_notification(label_dict, "Draft")
        return label_dict, []

    def update_status(self, label_id, new_status, performed_by):
        valid_transitions = {
            "Draft": ["Submitted"],
            "Submitted": ["Under Review"],
            "Under Review": ["Approved", "Rejected"],
            "Rejected": ["Draft"]
        }
        label = self.repo.get_by_id(label_id)
        current = label["status"]

        if new_status not in valid_transitions.get(current, []):
            return None, f"Cannot move from {current} to {new_status}"

        updated = self.repo.update_status(label_id, new_status)
        self.auditor.log(
            label_id, "STATUS_CHANGED",
            performed_by,
            f"{current} → {new_status}"
        )

        sap_result = None
        if new_status == "Approved":
            sap_result = self.sap.send_to_sap(updated)
            self.auditor.log(
                label_id, "SAP_POSTED",
                "system",
                f"SAP Material: {sap_result['sap_material_number']}"
            )
            self.notifier.send_approval_email(updated, sap_result)
        else:
            self.notifier.send_notification(updated, new_status)

        return {"label": updated, "sap": sap_result}, None

    def get_audit_trail(self, label_id):
        logs = list(audit_container.query_items(
            query="SELECT * FROM c WHERE c.label_id = @id ORDER BY c.timestamp ASC",
            parameters=[{"name": "@id", "value": label_id}],
            enable_cross_partition_query=True
        ))
        return logs


# ── Initialize Services ─────────────────────────────────────────
repo = LabelRepository(labels_container)
auditor = AuditLogger(audit_container)
validator = LabelValidator()
sap = SAPIntegration()
notifier = EmailNotifier()
service = LabelService(repo, auditor, validator, sap, notifier)


# ── Routes ───────────────────────────────────────────────────────
@app.route('/')
def home():
    return jsonify({
        "message": "Pharma Label Approval Workflow API",
        "version": "3.0",
        "endpoints": [
            "GET /labels",
            "POST /labels",
            "PUT /labels/<id>/status",
            "GET /labels/<id>/audit",
            "GET /auth/login",
            "GET /auth/user",
            "GET /auth/logout"
        ]
    })


# ── Auth Routes ──────────────────────────────────────────────────
@app.route('/auth/login')
def login():
    state = str(uuid.uuid4())
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={os.getenv('GOOGLE_CLIENT_ID')}"
        f"&redirect_uri={os.getenv('GOOGLE_REDIRECT_URI')}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&state={state}"
    )
    return redirect(auth_url)

@app.route('/auth/callback')
def auth_callback():
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "No code returned"}), 400

    # Exchange code for access token
    token_response = req.post(
        'https://oauth2.googleapis.com/token',
        data={
            'code': code,
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI'),
            'grant_type': 'authorization_code'
        }
    )
    tokens = token_response.json()

    if 'access_token' not in tokens:
        return jsonify({"error": "Failed to get access token", "details": tokens}), 400

    # Get user info from Google
    user_response = req.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f"Bearer {tokens['access_token']}"}
    )
    user_info = user_response.json()

    # Store user in server-side store
    token_id = str(uuid.uuid4())
    user_store[token_id] = {
        'email': user_info.get('email'),
        'name': user_info.get('name'),
        'picture': user_info.get('picture')
    }

    auditor.log(
        "system", "USER_LOGIN",
        user_info.get('email'),
        "SSO Login via Google OAuth"
    )

    # Redirect to frontend with token in URL
    return redirect(f'http://localhost:3000?token={token_id}')

@app.route('/auth/user')
def get_user():
    token = request.args.get('token') or request.headers.get('X-Auth-Token')
    user = user_store.get(token)
    if user:
        return jsonify({"user": user, "authenticated": True, "token": token})
    return jsonify({"user": None, "authenticated": False})

@app.route('/auth/logout')
def logout():
    token = request.args.get('token') or request.headers.get('X-Auth-Token')
    user = user_store.get(token)
    if user:
        auditor.log("system", "USER_LOGOUT", user['email'], "User logged out")
        del user_store[token]
    return jsonify({"message": "Logged out successfully"})


# ── Label Routes ─────────────────────────────────────────────────
@app.route('/labels', methods=['GET'])
@login_required
def get_labels():
    return jsonify(service.get_all_labels())

@app.route('/labels', methods=['POST'])
@login_required
def submit_label():
    data = request.json
    user = get_current_user()
    if not data.get('submitted_by'):
        data['submitted_by'] = user['name']
    label, errors = service.submit_label(data)
    if errors:
        return jsonify({"errors": errors}), 400
    return jsonify({
        "message": "Label submitted successfully!",
        "label": label
    }), 201

@app.route('/labels/<label_id>/status', methods=['PUT'])
@login_required
def update_status(label_id):
    data = request.json
    user = get_current_user()
    result, error = service.update_status(
        label_id,
        data.get("status"),
        user['email']
    )
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Status updated!", "result": result})

@app.route('/labels/<label_id>/audit', methods=['GET'])
@login_required
def get_audit(label_id):
    logs = service.get_audit_trail(label_id)
    return jsonify({"label_id": label_id, "audit_trail": logs})


if __name__ == '__main__':
    app.run(debug=True)