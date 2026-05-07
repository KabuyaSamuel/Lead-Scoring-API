````markdown
# AI Lead Qualification & Outreach System

This project is an AI-powered lead qualification and outreach automation system I built using:

- FastAPI
- scikit-learn
- n8n
- Airtable
- OpenAI
- Gmail automation

The goal was to explore how machine learning models can integrate with workflow automation tools in a practical business workflow.

Instead of building only a standalone ML model, I wanted the model to trigger real actions such as:
- lead routing
- CRM updates
- AI-generated communication
- automated outreach workflows

The project combines:
- AI engineering
- backend APIs
- workflow automation
- CRM integration
- cloud deployment

---

# What This System Does

The workflow automatically:

1. Receives inbound leads through a webhook
2. Scores them using a machine learning model
3. Classifies them as:
   - hot
   - warm
   - cold
4. Routes them through different automation paths
5. Generates personalized outreach emails using AI
6. Logs everything into Airtable

---

# System Architecture

```text
Inbound Lead
     ↓
n8n Webhook
     ↓
FastAPI Lead Scoring API
     ↓
Random Forest ML Model
     ↓
Lead Classification
     ↓
Conditional Routing in n8n
     ↓
Airtable CRM Logging
     ↓
OpenAI Email Generation
     ↓
Gmail Outreach
````

---

# Project Structure

```text
lead_scoring_api/
├── app/
│   ├── __init__.py
│   └── main.py                # FastAPI application
│
├── scripts/
│   └── train_model.py         # ML model training script
│
├── docs/
│   └── README.md              # Additional documentation
│
├── nginx/
│   └── default.conf           # Optional nginx config
│
├── tests/                     # Future API and workflow tests
│
├── lead_model.pkl             # Trained ML model
├── requirements.txt
├── build.sh
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

# Project Organization

I separated the project into logical layers to make it easier to maintain and extend later.

- `app/` contains the FastAPI application
- `scripts/` contains utility and ML training scripts
- `docs/` stores additional documentation
- `tests/` is reserved for future automated tests
- `nginx/` contains reverse proxy configuration for future deployment setups

I wanted the structure to stay scalable as the project grows beyond a single API file.

# Why I Built This

I wanted to experiment with combining:

* machine learning
* APIs
* workflow automation
* AI-generated actions

Most ML tutorials stop at predictions.

I wanted to push the prediction into a real workflow where the result automatically triggers:

* CRM logging
* lead routing
* email generation
* outreach actions

This project became a practical experiment in building AI-powered business automation systems.

---

# ML Model Overview

The lead scoring model uses a Random Forest classifier trained on synthetic lead data.

At the moment, the model uses weighted business logic to simulate real lead qualification behavior.

The idea was to prototype:

* feature engineering
* model inference
* workflow integration
* automation orchestration

before introducing real CRM conversion data later.

---

# Features Used for Lead Scoring

The model evaluates:

| Feature       | Description                                |
| ------------- | ------------------------------------------ |
| job_seniority | Individual → Manager → Director → C-Suite  |
| company_size  | Employee count range                       |
| budget_flag   | Whether budget was mentioned               |
| timeline      | Urgency level                              |
| pain_points   | Number of pain points described            |
| industry_fit  | Whether the lead matches target industries |

---

# Lead Scoring Logic

The synthetic scoring logic is based on weighted business rules.

```python
score = (
    job_seniority * 20 +
    company_size  * 15 +
    budget_flag   * 25 +
    timeline      * 15 +
    pain_points   * 5 +
    industry_fit  * 10
)
```

The trained model learns patterns from these examples and predicts:

| Tier | Meaning |
| ---- | ------- |
| 0    | Cold    |
| 1    | Warm    |
| 2    | Hot     |

---

# Local Setup

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/lead-scoring-api.git
cd lead-scoring-api
```

---

## 2. Create a Virtual Environment

### Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Train the Model

```bash
python scripts/train_model.py
```

Expected output:

```text
✅ Model trained and saved as lead_model.pkl
```

This generates:

```text
lead_model.pkl
```

This serialized model file is loaded by the FastAPI application during startup and used for lead classification.

---

## 5. Run the API Locally

```bash
uvicorn app.main:app --reload --port 8000
```

Open:

```text
http://localhost:8000
```

---

# API Documentation

FastAPI automatically generates Swagger docs.

Visit:

```text
http://localhost:8000/docs
```

You can:

* test endpoints
* inspect schemas
* send requests
* validate payloads

---

# API Endpoints

| Endpoint      | Method | Description               |
| ------------- | ------ | ------------------------- |
| `/`           | GET    | Root status               |
| `/health`     | GET    | Health check              |
| `/score-lead` | POST   | Score and classify a lead |

---

# Sample API Request

```bash
curl -X POST "http://localhost:8000/score-lead" \
-H "Content-Type: application/json" \
-d '{
  "name": "Jane Doe",
  "email": "jane@techcorp.io",
  "company": "TechCorp",
  "job_title": "VP of Operations",
  "industry": "SaaS",
  "company_size": 3,
  "budget_flag": 1,
  "timeline": 2,
  "pain_points": 4,
  "message": "We need to automate our CRM immediately."
}'
```

---

# Example API Response

```json
{
  "name": "Jane Doe",
  "email": "jane@techcorp.io",
  "company": "TechCorp",
  "job_title": "VP of Operations",
  "industry": "SaaS",
  "score": 89,
  "tier": "hot",
  "tier_code": 2,
  "routing_action": "immediate_outreach",
  "confidence": 0.98
}
```

---

# n8n Workflow Setup

The workflow file is:

```text
n8n_workflow.json
```

Import it into n8n using:

```text
Import from File
```

---

# n8n Workflow Logic

The workflow:

1. Receives lead data through a webhook
2. Sends the lead to the FastAPI scoring API
3. Receives:

   * score
   * tier
   * confidence
4. Routes the lead based on classification
5. Logs the lead into Airtable
6. Generates a personalized outreach email with OpenAI
7. Sends the email through Gmail

---

# Webhook Testing

## Test Mode

When using test mode:

```text
/webhook-test/lead-intake
```

you must click:

```text
Execute Workflow
```

inside n8n before sending requests.

Test webhooks only stay active for one request.

---

## Production Mode

Production webhook:

```text
/webhook/lead-intake
```

requires:

* workflow activation ON

---

# Test the Webhook from Terminal

```bash
curl -X POST "https://YOUR-N8N-INSTANCE.app.n8n.cloud/webhook-test/lead-intake" \
-H "Content-Type: application/json" \
-d '{
  "name": "Samuel Kabuya",
  "email": "samuel@test.com",
  "company": "SamTechHub",
  "job_title": "Automation Lead",
  "industry": "SaaS",
  "company_size": 2,
  "budget_flag": 1,
  "timeline": 2,
  "pain_points": 3,
  "message": "We need to automate our lead pipeline and CRM workflows urgently."
}'
```

---

# Airtable Setup

The workflow stores leads in Airtable.

Recommended fields:

| Field          | Type          |
| -------------- | ------------- |
| Name           | Text          |
| Email          | Email         |
| Company        | Text          |
| Job Title      | Text          |
| Industry       | Text          |
| Lead Score     | Number        |
| Tier           | Single Select |
| Confidence     | Number        |
| Routing Action | Text          |
| Email Subject  | Text          |
| Email Draft    | Long Text     |
| Status         | Single Select |

---

# Deploying to Render

## 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
```

Connect repository:

```bash
git remote add origin https://github.com/YOUR-USERNAME/lead-scoring-api.git
git branch -M main
git push -u origin main
```

---

## 2. Create a Render Web Service

Go to:

[https://render.com](https://render.com)

Create:

```text
New → Web Service
```

Connect your GitHub repository.

---

## 3. Configure Render

| Setting       | Value                                          |
| ------------- | ---------------------------------------------- |
| Runtime       | Python 3                                       |
| Build Command | `bash build.sh`                                |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

---

## 4. Deploy

Render will:

1. clone the repository
2. install dependencies
3. train the model
4. launch the API

---

# Docker Setup (Optional)

## Build Image

```bash
docker build -t lead-scoring-api .
```

---

## Run Container

```bash
docker run -p 8000:8000 lead-scoring-api
```

---

## Docker Compose

```bash
docker-compose up --build
```

Stop:

```bash
docker-compose down
```

---

# Current Limitations

At the moment:

* the model uses synthetic training data
* scoring logic is partially rule-based
* no persistent database is implemented yet
* there is no authentication layer on the API
* outreach emails are generated synchronously

---

# Future Improvements

Planned improvements include:

* retraining using real CRM conversion data
* LLM-based pain point extraction
* lead enrichment APIs
* Slack alerts for hot leads
* analytics dashboard
* feedback loop for continuous retraining
* API authentication and rate limiting
* vector-based lead similarity search

---

# Troubleshooting

| Problem                  | Fix                                       |
| ------------------------ | ----------------------------------------- |
| `lead_model.pkl` missing | Run `python scripts/train_model.py`               |
| Webhook 404              | Click "Execute Workflow" in n8n test mode |
| API connection failed    | Verify Render deployment URL              |
| Gmail errors             | Reconnect Gmail OAuth                     |
| Airtable errors          | Verify Airtable credentials               |
| OpenAI errors            | Verify API key                            |
| Slow first request       | Render free tier cold start               |

---

# Final Notes

This project was mainly an exploration of how:

* machine learning
* APIs
* workflow automation
* AI-generated communication

can work together inside a real automation pipeline.

The long-term goal is to evolve this into a more intelligent lead operations system powered by real-world conversion data and adaptive automation.

Yours Truly, 
Samuel Kabuya 
Cyber Name: P3ll0h read as Pelloh! 

```
```
