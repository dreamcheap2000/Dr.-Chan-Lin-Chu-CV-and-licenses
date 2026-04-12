# Running PHCEP Locally on macOS (Apple Silicon M2)

This guide walks you through running the full PHCEP stack on a **MacBook Air/Pro with an Apple Silicon M2 chip** (arm64). Two paths are covered:

- **Path A — Docker Compose (recommended):** all services in containers, minimal host-level setup.
- **Path B — Non-Docker local dev:** each service run natively on macOS for faster iteration.

> **Note:** Running PHCEP locally is ideal for development and demos. If you want PHCEP accessible publicly 24/7 without keeping your Mac on, see [`deployment.md`](./deployment.md) for cloud options.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone the repository](#2-clone-the-repository)
3. [Environment variables and secrets](#3-environment-variables-and-secrets)
4. [Path A — Docker Compose (recommended)](#4-path-a--docker-compose-recommended)
   - [Apple Silicon caveats](#apple-silicon-caveats-arm64-vs-amd64)
   - [Build and start](#build-and-start)
   - [Verify services are healthy](#verify-services-are-healthy)
   - [Stop the stack](#stop-the-stack)
5. [Path B — Non-Docker local dev](#5-path-b--non-docker-local-dev)
   - [Backend (Java/Maven)](#backend-javamaven)
   - [ML microservice (Python venv)](#ml-microservice-python-venv)
   - [Frontend (Node/Vite)](#frontend-nodevite)
6. [Accessing the UI and APIs](#6-accessing-the-ui-and-apis)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Prerequisites

Install the following tools on your M2 Mac before you begin.

### Homebrew (package manager)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# Follow the post-install instructions to add brew to your PATH
```

### Docker Desktop for Mac (Apple Silicon build)

Download the **Apple Silicon** edition from <https://www.docker.com/products/docker-desktop/>.

After installing, open Docker Desktop and verify:

- **Settings → General:** "Use Rosetta for x86/amd64 emulation on Apple Silicon" — **enable** this. It lets Docker pull and run `linux/amd64` images when a native `linux/arm64` image is not available.
- **Settings → Resources → Memory:** set to at least **6 GB** (8 GB recommended) for the full stack (Postgres + Redis + Spring Boot JVM + ML + frontend).

Verify Docker is working:

```bash
docker version          # should show both Client and Server
docker compose version  # should show v2.x
```

### Java 17 (required for Path B; also needed by `setup.sh` pre-flight check)

```bash
brew install openjdk@17
# Add to PATH — follow the caveats shown after install, e.g.:
echo 'export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
java -version   # should print openjdk 17.x.x
```

### Maven 3.9+

```bash
brew install maven
mvn -version
```

### Node.js 18+

```bash
brew install node@18
node -v    # v18.x.x
npm -v
```

### Python 3.10+ (required for Path B or local tooling)

macOS ships an older Python. Install a fresh one via Homebrew:

```bash
brew install python@3.10
python3 --version   # Python 3.10.x
```

---

## 2. Clone the repository

```bash
git clone https://github.com/dreamcheap2000/Dr.-Chan-Lin-Chu-CV-and-licenses.git
cd "Dr.-Chan-Lin-Chu-CV-and-licenses/CV and certificate/projects/PHCEP"
```

All paths in this guide are relative to this `PHCEP/` directory unless stated otherwise.

---

## 3. Environment variables and secrets

The stack reads secrets from a `.env` file in the PHCEP root. The `setup.sh` script creates a template automatically:

```bash
bash scripts/setup.sh
```

The script also performs a prerequisite check. If any tool is missing it will exit with an error — install the missing tool (see [Prerequisites](#1-prerequisites)) and re-run.

After the script runs, open the generated `.env` file and fill in real values:

```dotenv
# Required — generate a strong random value, e.g.:
#   openssl rand -base64 32
JWT_SECRET=REPLACE_WITH_256_BIT_BASE64_SECRET

# Optional — only needed if you use the LINE Messaging integration
LINE_CHANNEL_ACCESS_TOKEN=YOUR_LINE_CHANNEL_ACCESS_TOKEN
LINE_CHANNEL_SECRET=YOUR_LINE_CHANNEL_SECRET

# Required — any random string used for date-shift de-identification
DATE_SHIFT_SEED=REPLACE_WITH_RANDOM_SECRET
```

> **Security reminder:** Never commit `.env` to Git. The repository's `.gitignore` already excludes it, but double-check before pushing.

---

## 4. Path A — Docker Compose (recommended)

### Apple Silicon caveats (arm64 vs amd64)

| Image | Native arm64? | Notes |
|---|---|---|
| `postgres:15-alpine` | ✅ Yes | Official multi-arch image |
| `redis:7-alpine` | ✅ Yes | Official multi-arch image |
| `eclipse-mosquitto:2` | ✅ Yes | Official multi-arch image |
| `node:18-alpine` (frontend) | ✅ Yes | Official multi-arch image |
| Backend (`Dockerfile.backend`) | ✅ Yes | OpenJDK 17 has arm64 images |
| ML (`Dockerfile.ml`) | ⚠️ Partial | `python:3.10-slim` is arm64 but **PyTorch wheels** may need attention — see below |

**PyTorch on arm64 / Apple Silicon (important):**

`torch==2.6.0` in `platform/ml/requirements.txt` has official `linux/arm64` wheels on PyPI, so a native build should work. However if Docker Desktop pulls the image as `linux/amd64` (e.g., because Rosetta emulation is active and the build context platform is forced), you may see the wrong wheel downloaded and a slow or broken install.

To ensure the ML container builds natively on arm64, Docker Compose will automatically use the host platform (`linux/arm64`) when you add `--platform linux/arm64` or set the env variable. The easiest approach is to add to your shell before running `docker compose`:

```bash
export DOCKER_DEFAULT_PLATFORM=linux/arm64
```

If you hit a wheel-download error for PyTorch during `docker compose build`, the fallback is to use Rosetta (slower but reliable):

```bash
export DOCKER_DEFAULT_PLATFORM=linux/amd64
```

Alternatively, override just the ML service platform in `docker-compose.yml` (see [Troubleshooting](#7-troubleshooting)).

### Build and start

```bash
cd docker
docker compose up --build
```

The first build downloads base images and compiles the Spring Boot JAR — expect **5–15 minutes** on first run. Subsequent starts (without `--build`) take about 30 seconds.

To run in the background (detached mode):

```bash
docker compose up --build -d
```

Follow logs while running in detached mode:

```bash
docker compose logs -f
# or follow a single service:
docker compose logs -f backend
```

### Verify services are healthy

```bash
docker compose ps
```

All services should show `healthy` (or `running` for services without a healthcheck) after about 60–90 seconds.

Quick smoke tests:

```bash
# Backend health endpoint
curl http://localhost:8080/actuator/health

# ML service health endpoint
curl http://localhost:8081/health

# Frontend (should return HTML)
curl -s http://localhost:3000 | head -5
```

### Stop the stack

```bash
# Stop and remove containers (keeps named volume pgdata):
docker compose down

# Stop and also delete the Postgres data volume (full reset):
docker compose down -v
```

---

## 5. Path B — Non-Docker local dev

Use this path when you want faster hot-reload cycles or need to debug a specific service without rebuilding containers.

For this path you still need **Docker Desktop running** to host Postgres and Redis:

```bash
cd docker
docker compose up -d postgres redis
```

### Backend (Java/Maven)

```bash
cd platform/backend
mvn spring-boot:run \
  -Dspring-boot.run.profiles=dev \
  -Dspring-boot.run.jvmArguments="\
    -DJWT_SECRET=<your_jwt_secret> \
    -DPHCEP_ML_BASE_URL=http://localhost:8081 \
    -DSPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/phcep \
    -DSPRING_DATASOURCE_USERNAME=phcep \
    -DSPRING_DATASOURCE_PASSWORD=changeme \
    -DSPRING_DATA_REDIS_HOST=localhost"
```

The backend starts on **http://localhost:8080**.

> **M2 tip:** The Spring Boot Maven plugin runs the JVM natively on arm64 — no Rosetta needed. Compilation is fast on M2.

### ML microservice (Python venv)

```bash
cd platform/ml

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**PyTorch on M2 (native MPS acceleration):**

The `requirements.txt` pins `torch==2.6.0`. On Apple Silicon you can optionally install the CPU-only wheel (smaller, no CUDA):

```bash
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
```

Or install the standard wheel from PyPI (also works on arm64, includes MPS support):

```bash
pip install torch==2.6.0
```

If you see `"illegal hardware instruction"` errors, the CPU-only wheel from the `cpu` index is the most reliable fallback.

Start the ML service:

```bash
uvicorn api:app --reload --port 8081
```

The ML service starts on **http://localhost:8081**.

### Frontend (Node/Vite)

```bash
cd platform/frontend
npm install
npm run dev
```

The dev server starts on **http://localhost:3000** with hot-module replacement enabled.

Set the backend URL if needed (defaults to `http://localhost:8080`):

```bash
VITE_API_BASE=http://localhost:8080 npm run dev
```

---

## 6. Accessing the UI and APIs

| Service | URL | Notes |
|---|---|---|
| Frontend (React) | http://localhost:3000 | Main web application |
| Backend REST API | http://localhost:8080 | Spring Boot |
| API docs (Swagger) | http://localhost:8080/swagger-ui.html | OpenAPI UI |
| Backend health | http://localhost:8080/actuator/health | Spring Actuator |
| ML microservice | http://localhost:8081 | FastAPI |
| ML docs | http://localhost:8081/docs | Auto-generated FastAPI docs |
| ML health | http://localhost:8081/health | |
| PostgreSQL | localhost:5432 | DB: `phcep`, user: `phcep` |
| Redis | localhost:6379 | |
| MQTT broker | localhost:1883 | Eclipse Mosquitto |

---

## 7. Troubleshooting

### Docker Desktop not starting / containers crash immediately

- Make sure Docker Desktop is fully started (whale icon in menu bar is solid, not animated).
- Increase memory allocation: **Docker Desktop → Settings → Resources → Memory** → set to 6–8 GB.

### `docker compose up` fails on ML container build with wheel errors

The PyTorch wheel for the wrong architecture may have been downloaded. Try forcing the arm64 platform:

```bash
DOCKER_DEFAULT_PLATFORM=linux/arm64 docker compose up --build
```

Or add a `platform:` key to the `ml` service in `docker/docker-compose.yml`:

```yaml
ml:
  platform: linux/arm64
  build:
    ...
```

If you still see errors, use the amd64 image with Rosetta:

```bash
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose up --build
```

### Port already in use

Find and stop the process occupying the port:

```bash
# Example: port 8080 is busy
lsof -i :8080
kill -9 <PID>
```

Common conflicts:
- **3000:** another Node dev server or Gatsby
- **5432:** a local Postgres installation (`brew services stop postgresql@15`)
- **6379:** a local Redis installation (`brew services stop redis`)
- **8080:** Tomcat, another Spring Boot app, or a proxy tool

### Backend fails with `Connection refused` to Postgres

Postgres may still be starting. Wait for it to become healthy:

```bash
docker compose ps postgres   # wait until "healthy"
```

### `illegal hardware instruction` in ML service (Python path)

Install the CPU-only PyTorch wheel:

```bash
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
```

### `mvn: command not found` or `java: command not found`

Re-run the setup check and ensure your PATH is updated:

```bash
bash scripts/setup.sh
```

Then verify:

```bash
java -version
mvn -version
```

### `npm run dev` fails with `EADDRINUSE`

Port 3000 is in use. Either stop the other process or change the Vite port:

```bash
npm run dev -- --port 3001
```

### LINE webhook not working locally

LINE requires a public HTTPS URL for its webhook. During local development you can use [ngrok](https://ngrok.com/) to expose your backend:

```bash
ngrok http 8080
# Set the resulting HTTPS URL as webhook: https://<id>.ngrok.io/api/line/webhook
```

---

## Quick reference: start / stop

```bash
# --- Docker Compose path ---
# Start all services (first time, builds images)
cd "CV and certificate/projects/PHCEP/docker"
docker compose up --build -d

# Stop all services (keep data)
docker compose down

# Full reset (delete Postgres data)
docker compose down -v

# --- Non-Docker path ---
# Start infra only
docker compose up -d postgres redis

# Backend
cd platform/backend && mvn spring-boot:run ...

# ML
cd platform/ml && source .venv/bin/activate && uvicorn api:app --reload --port 8081

# Frontend
cd platform/frontend && npm run dev
```
