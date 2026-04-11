# Deployment Guide

## Local Development (Docker Compose)

### Prerequisites
- Docker 24+
- Docker Compose v2

### Steps

```bash
# 1. Clone and enter project
cd "CV and certificate/projects/PHCEP"

# 2. Copy and edit environment file
cp .env.example .env
# Edit .env with your secrets

# 3. Build and start all services
cd docker
docker compose up --build

# Services started:
#   postgres    :5432
#   redis       :6379
#   backend     :8080
#   ml          :8081
#   frontend    :3000
#   mosquitto   :1883
```

### Environment Variables (.env)

```dotenv
JWT_SECRET=replace-with-256-bit-base64-random-string
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret
DATE_SHIFT_SEED=replace-with-random-secret-string
```

---

## Manual Development Setup

### Backend (Spring Boot)

```bash
cd platform/backend
# Start PostgreSQL + Redis first (or use docker compose for just those)
docker compose -f ../../docker/docker-compose.yml up -d postgres redis

mvn spring-boot:run \
  -Dspring-boot.run.profiles=dev \
  -Dspring-boot.run.jvmArguments="\
    -DPHCEP_ML_BASE_URL=http://localhost:8081 \
    -DSPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/phcep"
```

### ML Microservice (Python)

```bash
cd platform/ml
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --reload --port 8081
```

### Frontend (React)

```bash
cd platform/frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

---

## Production Deployment

### Kubernetes (Phase 3)

Helm chart target structure:
```
k8s/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── backend-deployment.yaml
    ├── ml-deployment.yaml
    ├── frontend-deployment.yaml
    ├── postgres-statefulset.yaml
    └── redis-deployment.yaml
```

### GitHub Actions CI/CD

Workflow triggers:
- `push` to `main` → build + test + deploy to staging
- `release` tag → deploy to production

Required GitHub Secrets:
- `DOCKER_USERNAME`, `DOCKER_PASSWORD`
- `JWT_SECRET`, `DATE_SHIFT_SEED`
- `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_CHANNEL_SECRET`
- `KUBE_CONFIG` (for Kubernetes deployment)

---

## LINE Bot Setup

1. Create a LINE Messaging API channel at https://developers.line.biz/
2. Set webhook URL to `https://your-domain/api/line/webhook`
3. Enable "Use webhook" in LINE Developers console
4. Set `LINE_CHANNEL_ACCESS_TOKEN` and `LINE_CHANNEL_SECRET` in `.env`

---

## TON / Cocoon Payment (Optional — Phase 3)

Set in `application.yml`:
```yaml
phcep:
  payment:
    enabled: true
    ton:
      wallet-address: "EQ..."
```

Requires Cocoon SDK integration in `PaymentService.java` (stub provided).
Skip at initial launch by keeping `payment.enabled=false`.
