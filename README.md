# Jenkins Pipeline Template Library

A production-ready Python toolkit providing **15 reusable Jenkins pipeline templates** with a CLI tool, REST API, and intelligent recommendation engine.

---

## Features

- **15 templates** across 8 categories (CI, Deployment, Docker, Infrastructure, Database, Security, Release, Testing)
- **CLI tool** — list, inspect, generate, search, and get recommendations from the terminal
- **REST API** (FastAPI) — 8 endpoints including a `POST /recommend` endpoint for best-match template selection
- **File generator** — produces `Jenkinsfile` + all supporting files (Dockerfile, Helm chart, Terraform, etc.)
- **Recommendation engine** — keyword-based scoring to match templates to your project

---

## Quick Start

```bash
# Install
pip install -e .

# List all templates
jenkins-pipeline-lib list

# Get details on a template
jenkins-pipeline-lib info python-ci

# Generate files into your project
jenkins-pipeline-lib generate python-ci --output ./my-project

# Get template recommendation
jenkins-pipeline-lib recommend --description "Python Django REST API with Docker" --tag python --tag docker

# Start the API server
uvicorn jenkins_pipeline_lib.api.app:app --reload --port 8000
# Interactive docs: http://localhost:8000/docs
```

---

## Template Catalogue

| ID | Name | Category | Complexity |
|----|------|----------|------------|
| `python-ci` | Python CI Pipeline | CI | Moderate |
| `nodejs-ci` | Node.js CI Pipeline | CI | Moderate |
| `java-maven-ci` | Java Maven CI Pipeline | CI | Moderate |
| `java-gradle-ci` | Java Gradle CI Pipeline | CI | Moderate |
| `docker-build-push` | Docker Build & Push | Docker | Simple |
| `kubernetes-deploy` | Kubernetes Deployment | Deployment | Advanced |
| `terraform-iac` | Terraform Infrastructure | Infrastructure | Advanced |
| `ansible-deploy` | Ansible Deployment | Deployment | Moderate |
| `microservices-ci-cd` | Microservices CI/CD | CI/CD | Advanced |
| `static-site-deploy` | Static Site Deployment | Deployment | Simple |
| `database-migration` | Database Migration | Database | Moderate |
| `security-scan` | Security Scanning | Security | Advanced |
| `release-management` | Release Management | Release | Moderate |
| `multi-branch-pipeline` | Multi-Branch Pipeline | CI | Moderate |
| `performance-test` | Performance Testing | Testing | Moderate |

---

## CLI Commands

```bash
jenkins-pipeline-lib list                          # List all templates
jenkins-pipeline-lib list --category ci            # Filter by category
jenkins-pipeline-lib info <template-id>            # Show template details
jenkins-pipeline-lib generate <id> --output <dir>  # Generate files
jenkins-pipeline-lib generate <id> --param KEY=VAL # Override a parameter
jenkins-pipeline-lib recommend -d "..." -t tag     # Get recommendation
jenkins-pipeline-lib search <keyword>              # Search templates
jenkins-pipeline-lib categories                    # List categories
```

---

## REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/templates` | List all templates |
| GET | `/templates/{id}` | Template details |
| GET | `/templates/{id}/jenkinsfile` | Raw Jenkinsfile |
| GET | `/categories` | All categories |
| GET | `/categories/{name}/templates` | Templates by category |
| POST | `/recommend` | Best template for your project |
| GET | `/search?q=...` | Search by keyword |
| GET | `/docs` | Swagger UI |

### Recommend endpoint example

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"description": "Python Flask API with Docker to AWS ECS", "tags": ["python", "docker", "aws"], "top_n": 3}'
```

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v --cov=jenkins_pipeline_lib
```

---

## Project Structure

```
jenkins_pipeline_lib/
├── __init__.py
├── core/
│   ├── registry.py     # 15 template metadata definitions
│   ├── scorer.py       # Recommendation engine
│   └── generator.py    # Jenkinsfile + file generator
├── cli/
│   └── main.py         # CLI: list, info, generate, recommend, search
├── api/
│   └── app.py          # FastAPI REST API
└── templates/
tests/
    test_all.py         # 30+ tests
pyproject.toml
README.md
```
