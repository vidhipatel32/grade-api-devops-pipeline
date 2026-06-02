# Grade API - SIT753 DevOps Pipeline Project

Grade API is a Python Flask REST API for calculating student grades. It is designed for the SIT223/SIT753 High Distinction Jenkins DevOps pipeline task and includes build, test, code quality, security, deployment, release, monitoring, and alerting evidence.

## Tech Stack

- App: Python 3.11, Flask, Gunicorn
- Testing: pytest, pytest-cov
- Code quality: pylint with a minimum score gate
- Security: Bandit source scan and Trivy filesystem scan
- Containerisation: Docker and Docker Compose
- Monitoring: Prometheus, Grafana, Alertmanager

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health` | Health check for deployment smoke tests |
| GET | `/metrics` | Prometheus metrics endpoint |
| POST | `/grade` | Calculate grades for a list of marks |
| POST | `/grades/batch` | Calculate grades for multiple students |

### Example: POST `/grade`

```json
{
  "marks": [45, 55, 70, 85, 95]
}
```

### Example: POST `/grades/batch`

```json
{
  "students": [
    {"name": "Alice", "marks": [85, 90, 78]},
    {"name": "Bob", "marks": [45, 60, 55]}
  ]
}
```

## Grading Scale

| Mark | Grade | Description |
| --- | --- | --- |
| 85-100 | HD | High Distinction |
| 75-84 | D | Distinction |
| 65-74 | C | Credit |
| 50-64 | P | Pass |
| 0-49 | N | Fail |

## Jenkins Pipeline Stages

1. Checkout: pulls source from Git and records the commit.
2. Build: creates a tagged Docker image artifact.
3. Test: runs unit and API integration tests with JUnit and coverage reports.
4. Code Quality: runs pylint and fails the pipeline below the configured threshold.
5. Security: runs Bandit and Trivy, then archives the security reports.
6. Deploy: deploys the app to a staging Docker Compose environment.
7. Staging Smoke Test: verifies the staging health endpoint.
8. Release: creates a release Docker tag, Git tag, and release notes.
9. Deploy Production: promotes the release to the production Compose environment.
10. Monitoring: verifies Prometheus, Alertmanager, Grafana, and app metrics.

The assignment rubric names seven core areas: Build, Test, Code Quality, Security, Deploy, Release, and Monitoring. This Jenkinsfile uses a few extra helper stages to make the evidence clearer.

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

## Run Tests

```bash
pip install -r requirements-dev.txt
pytest test_app.py -v --cov=.
```

## Run with Docker

```bash
docker build -t grade-api:local .
docker run --rm -p 5000:5000 grade-api:local
```

## Deploy Staging

```bash
docker compose -p grade-api-staging -f docker-compose.staging.yml up -d
```

Staging app: http://localhost:5001/health

## Deploy Production with Monitoring

```bash
docker compose -p grade-api-prod -f docker-compose.production.yml up -d
```

- Production app: http://localhost:5000/health
- App metrics: http://localhost:5000/metrics
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093
- Grafana: http://localhost:3000, login `admin` / `admin123`

## HD Demo Evidence

For the assignment video and report, capture:

- Jenkins full pipeline screenshot showing all stages green.
- Docker image build tag, such as `grade-api:v1.0.<build-number>`.
- Jenkins JUnit test result and coverage artifact.
- Pylint report and pass/fail threshold.
- Bandit text report and Trivy JSON security report.
- Staging health check at `http://localhost:5001/health`.
- Production health check at `http://localhost:5000/health`.
- Prometheus targets page showing `grade-api` as up.
- Grafana dashboard showing live app metrics.
- Alertmanager page and an alert simulation, such as stopping the production container or generating repeated 500 responses.
