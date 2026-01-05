# Advanced Autonomics - AI Email Agent

A powerful, autonomous AI agent designed to intelligently manage and automate email outreach. Built with modern technologies to ensure reliability, safety, and scalability.

## 🚀 Features

- **Autonomous Outreach**: Automatically identifies eligible leads and sends personalized emails.
- **Intelligent Decision Making**: Uses **Ollama (LLMs)** to analyze leads and decide on the best engagement strategy.
- **Safety First**:
  - **Rate Limiting**: Configurable daily and hourly email limits.
  - **Business Hours**: only sends emails during specified business hours.
  - **Error Circuit Breaker**: Automatically pauses if error rates exceed a threshold.
- **Comprehensive Dashboard**: Real-time monitoring of agent status, email metrics, and decision logs.
- **Robust Architecture**: Built on **FastAPI** and **Celery** with **Redis** for reliable task queuing and scheduling.

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI
- **Task Queue**: Celery, Redis
- **Database**: SQLite (with SQLAlchemy)
- **AI/ML**: Ollama (Local LLM inference)
- **Containerization**: Docker & Docker Compose

## 📋 Prerequisites

Before deploying, ensure you have the following installed on your server:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## ⚡ Quick Start

For a detailed deployment guide, please refer to [AGENT_SETUP.md](AGENT_SETUP.md).

### 1. Clone & Configure

```bash
# Clone the repository
git clone <your-repo-url>
cd advanced-autonomics

# Create environment file
cp .env.example .env
```

Edit `.env` to set your specific configurations (Timezone, Limits, API keys).

### 2. Build & Launch

```bash
# Build and start services in detached mode
docker-compose up -d --build
```

### 3. Initialize Database

Run the migration script to set up the database schema:

```bash
# Using the provided utility script
docker-compose exec api python run_migration.py
```

## 🎮 Usage

### Accessing the Dashboard

Once running, access the Agent Dashboard at:
`http://<your-server-ip>:8000`

From here you can:
- **Start/Stop** the agent.
- View **Real-time Statistics**.
- Monitor **Agent Logs** and decisions.

### API Endpoints

- **Health Check**: `GET /health`
- **Agent Status**: `GET /agent/status`
- **Manual Trigger**: `POST /agent/run-now`

## ⚙️ Configuration

Key configurations in `agent_config.yaml` or `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `DAILY_EMAIL_LIMIT` | Max emails per day | 2000 |
| `BUSINESS_HOURS_START` | Start of sending window | 09:00 |
| `BUSINESS_HOURS_END` | End of sending window | 17:00 |
| `TIMEZONE` | Operational timezone | America/New_York |

## 🛡️ Safety Mechanisms

The agent is designed to be safe by default:
- **Duplicate Prevention**: Tracks all sent emails to avoid double-messaging.
- **Bounce Detection**: (If configured) Stops messaging invalid addresses.
- **Manual Override**: Immediate "Stop" button available on the dashboard.

## 📄 License

[MIT License](LICENSE) (or your specific license)
