# Sentinel AI — AI-Powered Incident Management Platform

<div align="center">

# 🚨 Sentinel AI

### Intelligent Incident Detection, Analysis & Remediation Platform

AI-powered incident management system built for DevOps, SRE, and Infrastructure teams to detect, analyze, and resolve production incidents in real time.

</div>

---

# 📌 Overview

Sentinel AI is a modern AI-powered incident management platform that helps engineering teams monitor infrastructure failures, analyze production incidents, correlate logs, and generate intelligent remediation workflows automatically.

The platform simulates real-world enterprise infrastructure environments involving:

- Kubernetes
- Redis
- PostgreSQL
- API Gateways
- Authentication Services
- CI/CD Deployments

Sentinel AI continuously processes infrastructure logs and incidents using AI models to:

✅ Detect anomalies  
✅ Correlate failures  
✅ Predict incident severity  
✅ Generate remediation steps  
✅ Create incident timelines  
✅ Produce automated post-mortem reports

---

# ⚡ Core Features

## 🧠 AI-Powered Incident Analysis

- Root cause detection
- AI-generated remediation
- Severity prediction
- Failure correlation engine
- Intelligent incident summarization
- Automated postmortem generation

---

## 📊 Real-Time Monitoring Dashboard

- Incident analytics
- MTTR tracking
- Infrastructure metrics
- Severity distribution
- Live anomaly monitoring
- Timeline-based visualization

---

## 🔔 Webhook-Based Real-Time Processing

External infrastructure systems can push logs and alerts directly into Sentinel AI using webhooks.

Supported integrations:
- Kubernetes
- Redis
- PostgreSQL
- CI/CD pipelines
- Monitoring tools
- API gateways
- Custom infrastructure services

---

# 🔄 AI Failover Architecture

Sentinel AI uses a resilient AI failover system to prevent analysis downtime.

## Primary AI Engine
- Groq API (LLM Inference)

## Fallback AI Engine
- HuggingFace Transformers
- FLAN-T5
- Microsoft Transformer Models

If Groq API becomes unavailable:
1. The platform automatically switches to local fallback inference
2. Incident processing continues
3. AI remediation remains operational

This ensures high availability during AI provider outages.

---

# 🏗️ System Architecture

```txt
Infrastructure Services
(Kubernetes / Redis / PostgreSQL / APIs)
                    │
                    ▼
          Webhook Ingestion Layer
                    │
                    ▼
            Django REST API
                    │
 ┌──────────────────┴──────────────────┐
 │                                     │
 ▼                                     ▼
Real-Time Log Engine           Incident Processor
 │                                     │
 ▼                                     ▼
AI Analysis Pipeline ─────────► Severity Engine
 │
 ├── Groq LLM API
 │
 └── HuggingFace Fallback Models
      (FLAN-T5 / Transformers)
                    │
                    ▼
          Root Cause Detection
                    │
                    ▼
         Remediation Generator
                    │
                    ▼
       Timeline & Postmortem Engine
                    │
                    ▼
            Dashboard Interface
```

---

# 🛠️ Tech Stack

## Backend
- Django
- Django REST Framework

## AI / NLP
- Groq API
- HuggingFace Transformers
- FLAN-T5
- Microsoft Transformer Models

## Infrastructure
- Redis
- Webhooks
- Real-Time Log Streaming

## Database
- SQLite
- PostgreSQL

## Frontend
- HTML
- CSS
- JavaScript

---

# 🔌 Webhook Integration

Sentinel AI can receive real-time infrastructure logs through webhooks.

## Example Webhook Request

```bash
curl -X POST http://localhost:8000/api/webhooks/incidents/ \
-H "Content-Type: application/json" \
-d '{
  "service": "payment-gateway",
  "severity": "critical",
  "message": "Redis timeout after 5000ms",
  "timestamp": "2026-05-24T18:24:13Z"
}'
```

---

# 🚨 Example Incident Workflow

## Step 1 — Infrastructure Failure

A Kubernetes deployment introduces unstable Redis behavior and PostgreSQL pool exhaustion.

---

## Step 2 — Log Ingestion

Infrastructure logs are streamed into Sentinel AI through webhooks.

---

## Step 3 — AI Correlation

The AI engine correlates:
- Redis timeout spikes
- PostgreSQL saturation
- API latency anomalies
- Kubernetes CrashLoopBackOff events

---

## Step 4 — Root Cause Detection

Sentinel AI identifies:

> PostgreSQL connection pool exhaustion causing cascading infrastructure instability.

---

## Step 5 — AI Remediation

Suggested remediation:
- Rollback deployment
- Restart unhealthy pods
- Scale PostgreSQL pools
- Isolate Redis traffic

---

## Step 6 — Automated Postmortem

The platform generates:
- Incident timeline
- Root cause analysis
- AI remediation summary
- Lessons learned
- Severity report

---

# 📈 Dashboard Features

- AI Incident Insights
- Infrastructure Monitoring
- MTTR Metrics
- Real-Time Logs
- Severity Tracking
- Root Cause Reports
- Timeline Analysis
- Remediation Suggestions

---

# 🧪 Example AI Incident

## Incident Title
Kubernetes Multi-Service Failure Causing Payment API Downtime

## Severity
Critical

## AI Confidence Score
94%

## Root Cause
PostgreSQL connection pool exhaustion combined with Redis timeout amplification triggered cascading pod instability.

---

# 🚀 Future Improvements

- Kubernetes-native deployment
- Prometheus integration
- Grafana dashboards
- Slack/Discord alerts
- Vector database support
- Multi-agent AI workflows
- Autonomous remediation execution
- RAG-based incident memory

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/Piyush70-coderyeah.git
cd sentinel-ai
```

---

## Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run Server

```bash
python manage.py runserver
```

---

# 📸 Project Screenshots

- AI Monitoring Dashboard
- Incident Creation Workflow
- AI Root Cause Analysis
- Timeline & Remediation Engine
- Automated Postmortem Reports

---

# 🎯 Why This Project Matters

Modern infrastructure generates massive operational data every second.

Sentinel AI demonstrates how AI can:
- reduce incident response time
- automate infrastructure analysis
- improve operational visibility
- assist DevOps and SRE teams during production failures

This project combines:
- AI Engineering
- Backend Development
- DevOps Concepts
- Infrastructure Monitoring
- Incident Automation

into a unified enterprise-style platform.

---

# 👨‍💻 Author

## Piyush Sharma

GitHub:
https://github.com/Piyush70-coderyeah

---
