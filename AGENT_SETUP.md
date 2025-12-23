# 🤖 AI Agent Setup Guide

Complete guide to deploying and running the AI email agent.

---

## 📋 Prerequisites

Before starting, ensure you have:
- Docker & Docker Compose installed
- Existing Advanced Autonomics project
- Leads imported in database
- Basic understanding of your email limits

---

## 🔧 Installation Steps

### **Step 1: Backup Your Database**

```bash
# CRITICAL: Backup before migration
cp data/data.db data/data.db.backup.$(date +%Y%m%d)
```

### **Step 2: Update Code Files**

Replace/create all files from the artifacts:

1. **New folders to create:**
   ```bash
   mkdir -p app/agent
   mkdir -p app/utils
   mkdir -p migrations
   ```

2. **Files to replace:**
   - `app/models/lead.py` - Modified with agent fields
   - `app/models/__init__.py` - Import new models
   - `app/worker/celery_app.py` - Add beat schedule
   - `app/main.py` - Register agent routes
   - `app/static/index.html` - New dashboard
   - `docker-compose.yml` - Updated services
   - `.env` - Add agent variables
   - `requirements.txt` - New dependencies

3. **New files to create:**
   - `app/models/agent_config.py`
   - `app/models/agent_action_log.py`
   - `app/agent/__init__.py`
   - `app/agent/agent_runner.py`
   - `app/agent/decision_engine.py`
   - `app/agent/safety_controller.py`
   - `app/agent/state_manager.py`
   - `app/utils/time_utils.py`
   - `app/utils/rate_limiter.py`
   - `app/routes/agent_routes.py`
   - `app/worker/agent_tasks.py`
   - `app/schemas/agent_schema.py`
   - `app/config.py`
   - `agent_config.yaml`
   - `migrations/add_agent_fields.sql`
   - `run_migration.py`

### **Step 3: Run Database Migration**

```bash
# Option A: Using Python script (RECOMMENDED)
python run_migration.py

# Option B: Using SQL directly
sqlite3 data/data.db < migrations/add_agent_fields.sql

# Verify migration
sqlite3 data/data.db "PRAGMA table_info(leads);"
sqlite3 data/data.db "SELECT * FROM agent_config;"
```

### **Step 4: Install New Dependencies**

```bash
pip install -r requirements.txt
```

Or if using Docker:
```bash
docker-compose build
```

### **Step 5: Configure Agent Settings**

Edit `agent_config.yaml`:

```yaml
limits:
  max_emails_per_day: 50  # Set your limit
  max_emails_per_hour: 10

timing:
  business_hours_start: "09:00"  # Your timezone
  business_hours_end: "17:00"
  timezone: "America/New_York"  # Change to your timezone
```

Edit `.env`:

```bash
AGENT_ENABLED=true
DAILY_EMAIL_LIMIT=50
BUSINESS_HOURS_START=09:00
BUSINESS_HOURS_END=17:00
TIMEZONE=America/New_York
```

### **Step 6: Start Services**

```bash
# Stop old services
docker-compose down

# Start with new configuration
docker-compose up -d

# Check logs
docker logs api -f
docker logs worker -f
docker logs beat -f
```

---

## ✅ Verification Checklist

### **1. Database Check**

```bash
# Check agent config exists
sqlite3 data/data.db "SELECT * FROM agent_config;"

# Check leads have new fields
sqlite3 data/data.db "PRAGMA table_info(leads);"

# Count agent-enabled leads
sqlite3 data/data.db "SELECT COUNT(*) FROM leads WHERE agent_enabled = 1;"
```

### **2. API Check**

```bash
# Check health
curl http://localhost:8000/health

# Check agent status
curl http://localhost:8000/agent/status

# Should return JSON with agent info
```

### **3. Dashboard Check**

Open browser: `http://localhost:8000`

You should see:
- ✅ Agent Control Panel at top
- ✅ Status indicator (red = stopped)
- ✅ Start/Stop/Pause buttons
- ✅ Email metrics (0/50 daily, etc.)
- ✅ Lead statistics

### **4. Celery Check**

```bash
# Check Celery Beat schedule
docker logs beat | grep "Scheduler: Sending"

# Check worker is receiving tasks
docker logs worker | grep "agent_cycle_task"
```

---

## 🚀 Starting the Agent

### **Method 1: Via Dashboard (Recommended)**

1. Open `http://localhost:8000`
2. Click **▶️ Start** button in Agent Control Panel
3. Confirm dialog
4. Agent status should turn green: "Agent Running"

### **Method 2: Via API**

```bash
# Start agent
curl -X POST http://localhost:8000/agent/start

# Check status
curl http://localhost:8000/agent/status

# Run one cycle manually
curl -X POST http://localhost:8000/agent/run-now
```

### **Method 3: Via Python**

```python
import requests

# Start agent
response = requests.post("http://localhost:8000/agent/start")
print(response.json())

# Run cycle
response = requests.post("http://localhost:8000/agent/run-now")
print(response.json())
```

---

## 📊 Monitoring the Agent

### **Dashboard Monitoring**

1. **Agent Control Panel:**
   - Status indicator (green = running)
   - Emails today: X/50
   - This hour: X/10
   - Last run: timestamp

2. **Agent Logs Tab:**
   - See every decision made
   - Which leads contacted
   - Success/failure status

3. **Auto-refresh:**
   - Status updates every 10 seconds automatically

### **Log Files**

```bash
# Watch agent decisions
docker logs worker -f | grep "Decision engine"

# Watch email sending
docker logs worker -f | grep "Email queued"

# Watch errors
docker logs worker -f | grep "ERROR"
```

---

## ⚠️ Important Safety Notes

### **Rate Limits**

Agent respects these limits:
- **Daily limit:** 50 emails (configurable)
- **Hourly limit:** 10 emails (configurable)
- **Per lead:** Max 3 follow-ups
- **Wait time:** 3 days between emails

### **Business Hours**

Agent only sends during:
- **Hours:** 9 AM - 5 PM (your timezone)
- **Days:** Monday - Friday
- **Configurable** in `agent_config.yaml`

### **Safety Controls**

Agent automatically stops if:
- Error rate > 10%
- Too many bounces
- Manual emergency stop
- Daily limit reached

---

## 🧪 Testing the Agent

### **Test 1: Dry Run (No Emails)**

```bash
# Check what agent would do
curl -X POST http://localhost:8000/agent/run-now

# Check logs to see decisions
curl http://localhost:8000/agent/logs?limit=10
```

### **Test 2: Send to Test Lead**

```bash
# Add a test lead with your email
curl -X POST http://localhost:8000/leads/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your.email@test.com",
    "first_name": "Test",
    "last_name": "User",
    "company": "Test Co",
    "industry": "Glassworks"
  }'

# Start agent
curl -X POST http://localhost:8000/agent/start

# Wait 30 seconds, check your email
# Should receive AI-generated email
```

### **Test 3: Verify Business Hours**

```bash
# Temporarily disable business hours check
curl -X PATCH http://localhost:8000/agent/config \
  -H "Content-Type: application/json" \
  -d '{"respect_business_hours": false}'

# Run agent
curl -X POST http://localhost:8000/agent/run-now

# Re-enable
curl -X PATCH http://localhost:8000/agent/config \
  -H "Content-Type: application/json" \
  -d '{"respect_business_hours": true}'
```

---

## 🐛 Troubleshooting

### **Agent Not Starting**

```bash
# Check config exists
curl http://localhost:8000/agent/status

# Check logs
docker logs api | grep -i error
docker logs worker | grep -i error

# Restart services
docker-compose restart
```

### **No Emails Being Sent**

Possible causes:

1. **Rate limit reached:**
   ```bash
   curl http://localhost:8000/agent/status
   # Check: emails_today vs daily_limit
   ```

2. **Outside business hours:**
   - Check current time vs configured hours
   - Temporarily disable: `respect_business_hours: false`

3. **No eligible leads:**
   ```bash
   # Check lead status
   sqlite3 data/data.db "SELECT status, COUNT(*) FROM leads GROUP BY status;"
   
   # Check agent-enabled leads
   sqlite3 data/data.db "SELECT COUNT(*) FROM leads WHERE agent_enabled = 1 AND agent_paused = 0;"
   ```

4. **Ollama timeout:**
   ```bash
   # Test Ollama
   curl http://localhost:11434/api/generate -d '{"model":"llama3","prompt":"Hello"}'
   
   # If slow, increase timeout in ollama_service.py
   ```

### **Agent Keeps Pausing**

Check error rate:
```bash
curl http://localhost:8000/agent/statistics

# If error_rate > 10%, agent auto-pauses
# Fix underlying issues, then resume
curl -X POST http://localhost:8000/agent/resume
```

### **Database Lock Errors**

SQLite can have concurrency issues:
```bash
# Stop all services
docker-compose down

# Backup database
cp data/data.db data/data.db.backup

# Restart
docker-compose up -d
```

---

## 🔄 Common Operations

### **Pause Agent Temporarily**

```bash
curl -X POST http://localhost:8000/agent/pause
```

### **Resume Agent**

```bash
curl -X POST http://localhost:8000/agent/resume
```

### **Stop Agent**

```bash
curl -X POST http://localhost:8000/agent/stop
```

### **Update Configuration**

```bash
# Change daily limit
curl -X PATCH http://localhost:8000/agent/config \
  -H "Content-Type: application/json" \
  -d '{"daily_email_limit": 100}'

# Change business hours
curl -X PATCH http://localhost:8000/agent/config \
  -H "Content-Type: application/json" \
  -d '{
    "business_hours_start": "08:00",
    "business_hours_end": "18:00"
  }'
```

### **Reset Daily Counters (Testing)**

```bash
curl -X POST http://localhost:8000/agent/reset-counters
```

### **View Agent Logs**

```bash
# Recent actions
curl http://localhost:8000/agent/logs?limit=50

# Statistics
curl http://localhost:8000/agent/statistics
```

---

## 📈 Performance Tips

### **Optimize Ollama**

1. Pre-load model:
   ```bash
   docker exec ollama ollama pull llama3
   ```

2. Keep container warm:
   ```bash
   # Add to docker-compose.yml healthcheck
   ```

### **Tune Agent Frequency**

Edit `.env`:
```bash
# Check every 10 minutes instead of 5
AGENT_CHECK_INTERVAL=10

# Check inbox every 30 minutes
INBOX_CHECK_INTERVAL=30
```

Restart:
```bash
docker-compose restart beat
```

### **Batch Processing**

Agent automatically batches:
- Sends up to 10 emails per cycle
- Respects hourly limits
- Processes highest priority first

---

## 🎯 Next Steps

Now that agent is running:

1. **Monitor for 24 hours:**
   - Check dashboard regularly
   - Verify emails being sent
   - Watch for errors

2. **Fine-tune settings:**
   - Adjust business hours
   - Set comfortable daily limits
   - Tune follow-up delays

3. **Add production SMTP:**
   - Switch from GreenMail to real SMTP
   - Update `.env` with production credentials

4. **Scale up:**
   - Import more leads
   - Increase daily limits gradually
   - Monitor deliverability

---

## 📞 Support

If issues persist:

1. Check logs: `docker logs api worker beat`
2. Verify database: `sqlite3 data/data.db`
3. Test API: `curl http://localhost:8000/health`
4. Review this guide again

Agent is now autonomous! 🎉