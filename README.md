# 💊 Enterprise Label Approval System

![CI/CD](https://github.com/krishna2198-dotcom/enterprise-label-approval-system/actions/workflows/deploy.yml/badge.svg?branch=main)

A full-stack enterprise workflow application simulating pharmaceutical label approval systems like **Perigord GLAMS** and **Loftware**, integrated with **SAP**, **SendGrid**, and **Google OAuth SSO** — built on Azure cloud infrastructure.

> Built to demonstrate SaaS engineering, cloud-native development, GxP compliance concepts, and enterprise integration patterns.

---

## 🎯 What This Project Demonstrates

| Concept | Implementation |
|---|---|
| SaaS Integration | SendGrid (email), Google OAuth (SSO) |
| Enterprise Workflow | Label approval pipeline with controlled transitions |
| SAP Integration | Automated SAP material number generation on approval |
| GxP Compliance | Immutable audit trail with timestamp and user attribution |
| OOP / MVC Architecture | Model → Repository → Service → Controller layers |
| Cloud Infrastructure | Azure CosmosDB, Azure App Service |
| CI/CD Automation | GitHub Actions pipeline |
| Data Validation | IQ/OQ/PQ simulation via LabelValidator |
| Identity Management | Google OAuth 2.0 SSO with access control |

---

## 🏗️ Architecture

```
[React.js Frontend]
        ↓  REST API calls (X-Auth-Token header)
[Flask Backend — OOP/MVC]
        ↓              ↓              ↓              ↓
[CosmosDB]      [SendGrid]     [Google OAuth]  [SAP Simulation]
(Label Data)    (Email SaaS)   (SSO / Identity) (ERP Integration)
        ↓
[GitHub Actions CI/CD]
```

### OOP / MVC Layer Breakdown

| Layer | Class | Responsibility |
|---|---|---|
| Model | `Label` | Data structure and serialization |
| Repository | `LabelRepository` | All CosmosDB operations |
| Validator | `LabelValidator` | Input validation (IQ/OQ/PQ simulation) |
| Service | `LabelService` | Business logic and orchestration |
| Notifier | `EmailNotifier` | SendGrid SaaS email integration |
| Integration | `SAPIntegration` | SAP ERP posting simulation |
| Controller | `Flask Routes` | HTTP request/response handling |
| Audit | `AuditLogger` | GxP-compliant immutable audit trail |

---

## 🔄 Workflow

```
Draft → Submitted → Under Review → Approved → SAP Posted
                                ↘ Rejected → Draft
```

- Every transition is **controlled** — stages cannot be skipped
- Every action is **logged** in an immutable audit trail
- **Email notification** sent at every stage change via SendGrid
- **SAP material number** auto-generated on approval
- Only **authenticated users** (Google SSO) can access the system

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React.js, JavaScript |
| Backend | Python 3.10, Flask |
| Database | Azure CosmosDB (NoSQL) |
| Email SaaS | SendGrid REST API |
| Authentication | Google OAuth 2.0 / OpenID Connect |
| CI/CD | GitHub Actions |
| Cloud | Microsoft Azure (App Service, CosmosDB) |
| Version Control | Git & GitHub |

---

## 📁 Project Structure

```
enterprise-label-approval-system/
├── backend/
│   ├── app.py              # Full backend — Models, Repository, Service, Routes
│   ├── requirements.txt    # Python dependencies
│   ├── startup.txt         # Azure App Service startup command
│   └── .env                # Environment variables (not committed)
├── frontend/
│   ├── src/
│   │   └── App.js          # React frontend — Login, Workflow UI, Audit Trail
│   └── package.json
└── .github/
    └── workflows/
        └── deploy.yml      # CI/CD Pipeline
```

---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- Azure CosmosDB account (free serverless tier)
- SendGrid account (free — 100 emails/day)
- Google Cloud OAuth credentials

---

### STEP 1 — Clone the repository
```bash
git clone https://github.com/krishna2198-dotcom/enterprise-label-approval-system.git
cd enterprise-label-approval-system
```

---

### STEP 2 — Set up CosmosDB containers
In your Azure CosmosDB account → Data Explorer → Create:
- Database: `taskdb`
- Container 1: `labels` (partition key: `/id`)
- Container 2: `audit_logs` (partition key: `/id`)

---

### STEP 3 — Set up Google OAuth
1. Go to https://console.cloud.google.com
2. Create a project → APIs & Services → Credentials
3. Create OAuth Client ID (Web application)
4. Add redirect URI: `http://localhost:5000/auth/callback`
5. Copy Client ID and Client Secret

---

### STEP 4 — Set up SendGrid
1. Go to https://sendgrid.com → Sign up free
2. Settings → API Keys → Create API Key
3. Settings → Sender Authentication → Verify your email

---

### STEP 5 — Create backend `.env` file
```bash
cd backend
```
Create a file named `.env` with:
```
COSMOS_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
COSMOS_KEY=your_cosmos_primary_key
COSMOS_DATABASE=taskdb
SENDGRID_API_KEY=your_sendgrid_api_key
SENDER_EMAIL=your-verified-email@gmail.com
NOTIFY_EMAIL=your-email@gmail.com
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/callback
FLASK_SECRET_KEY=any-random-secret-string
```

---

### STEP 6 — Run the Backend
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
python app.py
```
Backend runs at: `http://127.0.0.1:5000`

---

### STEP 7 — Run the Frontend
Open a new terminal:
```bash
cd frontend
npm install
npm start
```
Frontend runs at: `http://localhost:3000`

---

### STEP 8 — Open the app
Go to `http://localhost:3000` → Click **Sign in with Google** → Start using the workflow!

---

## 🔌 API Endpoints

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| GET | `/` | No | API health check and info |
| GET | `/auth/login` | No | Redirect to Google SSO |
| GET | `/auth/callback` | No | Google OAuth callback |
| GET | `/auth/user` | No | Get current user info |
| GET | `/auth/logout` | No | Logout and clear session |
| GET | `/labels` | ✅ Yes | Get all labels |
| POST | `/labels` | ✅ Yes | Submit new label |
| PUT | `/labels/<id>/status` | ✅ Yes | Update label status |
| GET | `/labels/<id>/audit` | ✅ Yes | Get full audit trail |

---

## 🔐 Authentication Flow

```
User clicks "Sign in with Google"
        ↓
Redirected to Google OAuth
        ↓
Google verifies identity
        ↓
Backend exchanges code for access token
        ↓
User info fetched from Google
        ↓
Server-side token generated and stored
        ↓
Frontend stores token in localStorage
        ↓
All API calls send token in X-Auth-Token header
```

---

## 📋 Audit Trail Example

Every label action is logged with full traceability:

```
CREATED          by Krishna          — Label submitted for review
STATUS_CHANGED   by reviewer         — Draft → Submitted
STATUS_CHANGED   by reviewer         — Submitted → Under Review
STATUS_CHANGED   by reviewer         — Under Review → Approved
SAP_POSTED       by system           — SAP Material: MAT-0DF1CAA8
```

---

## 🏥 GxP Compliance Concepts Demonstrated

| GxP Principle | Implementation |
|---|---|
| Data Integrity (ALCOA+) | Audit trail — Attributable, Contemporaneous, Original |
| Change Control | Controlled workflow transitions — no stage skipping |
| IQ/OQ/PQ Simulation | LabelValidator checks required fields and valid values |
| Audit Trail | Every action logged with user, timestamp, and details |
| Access Control | SSO authentication — only approved users can access |
| Documentation | Clear README, code comments, audit logs |

---

## ⚙️ CI/CD Pipeline

GitHub Actions runs automatically on every push to `main`:

```
Push to main
     ↓
┌─────────────────┐    ┌──────────────────┐
│  Backend Check  │    │  Frontend Build  │
│  Python 3.10    │    │  Node.js 18      │
│  Syntax check   │    │  npm install     │
│  app.py         │    │  npm run build   │
└─────────────────┘    └──────────────────┘
```

---

## 🌐 Part of Azure Cloud Portfolio

This is the flagship project of my Azure Cloud Developer Portfolio.

🔗 **Full Portfolio:** https://github.com/krishna2198-dotcom/azure-cloud-portfolio

### Other Projects
| Project | Description |
|---|---|
| [azure-cloud-api](https://github.com/krishna2198-dotcom/azure-cloud-api) | Flask REST API on Azure with Application Insights |
| [azure-sql-api](https://github.com/krishna2198-dotcom/azure-sql-api) | Flask API with Azure SQL Database |
| [azure-storage-api](https://github.com/krishna2198-dotcom/azure-storage-api) | File upload API with Azure Blob Storage |

---

## 👤 Author

**Krishnaraja Delanthamajalu**
- GitHub: [@krishna2198-dotcom](https://github.com/krishna2198-dotcom)
- LinkedIn: [linkedin.com/in/krishnaraja-delanthamajalu](https://linkedin.com/in/krishnaraja-delanthamajalu)
