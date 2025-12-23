# ✅ AI Agent Implementation Checklist

Complete checklist for implementing the autonomous email agent.

---

## 📦 Phase 1: File Setup (30 minutes)

### **New Files to Create**

Copy these artifacts and create new files:

- [ ] `app/models/agent_config.py` - Agent config model
- [ ] `app/models/agent_action_log.py` - Action logging model
- [ ] `app/agent/__init__.py` - Agent module init
- [ ] `app/agent/agent_runner.py` - Main agent loop (340 lines)
- [ ] `app/agent/decision_engine.py` - Decision logic (280 lines)
- [ ] `app/agent/safety_controller.py` - Safety checks (180 lines)
- [ ] `app/agent/state_manager.py` - State transitions (220 lines)
- [ ] `app/utils/time_utils.py` - Time utilities (130 lines)
- [ ] `app/utils/rate_limiter.py` - Rate limiting (120 lines)
- [ ] `app/routes/agent_routes.py` - Agent API (320 lines)
- [ ] `app/worker/agent_tasks.py` - Celery tasks (200 lines)
- [ ] `app/schemas/agent_schema.py` - Pydantic schemas (50 lines)
- [ ] `app/config.py` - Configuration loader (90 lines)
- [ ] `agent_config.yaml` - Agent settings file (120 lines)
- [ ] `migrations/add_agent_fields.sql` - Database migration (150 lines)
- [ ] `run_migration.py` - Migration runner (40 lines)
- [ ] `AGENT_SETUP.md` - Setup documentation
- [ ] `setup_agent.sh` - Quick setup script

### **Files to Modify**

Replace these existing files with updated versions:

- [ ] `app/models/lead.py` - Add 13 new agent fields
- [ ] `app/models/__init__.py` - Import new models
- [ ] `app/schemas/lead_schema.py` - Add agent field schemas
- [ ] `app/worker/celery_app.py` - Add beat schedule
- [ ] `app/main.py` - Register agent routes, init config
- [ ] `app/static/index.html` - New dashboard with agent controls
- [ ] `docker-compose.yml` - Add agent config volume, update services
- [ ] `.env` - Add agent environment variables
- [ ] `requirements.txt` - Add new dependencies

---

## 🗄️ Phase 2: Database Migration (10 minutes)

### **Backup Database**

- [ ] Create backup: `cp data/data.db data/data.db.backup`
- [ ] Verify backup exists

### **Run Migration**

Choose one method:

**Option A - Python Script (Recommended):**
```bash
python run_migration.py
```

**Option B - Direct SQL:**
```bash
sqlite3 data/data.db < migrations/add_agent_fields.sql
```

### **Verify Migration**

- [ ] Check agent_config table: `sqlite3 data/data.db "SELECT * FROM agent_config;"`
- [ ] Check lead fields: `sqlite3 data/data.db "PRAGMA table_info(leads);"`
- [ ] Should see new columns: `agent_enabled`, `agent_paused`, `next_agent_check_at`, etc.

---

## 🐳 Phase 3: Docker Setup (15 minutes)

### **Install Dependencies**

- [ ] Update requirements: `pip install -r requirements.txt`
- [ ] Or rebuild Docker: `docker-compose build`

### **Configuration**

- [ ] Edit `agent_config.yaml` - Set your timezone, limits
- [ ] Edit `.env` - Add agent variables
- [ ] Verify `AGENT_ENABLED=true` in `.env`

### **Start Services**

```bash
docker-compose down
docker-compose up -d
```

- [ ] Check all containers running: `docker ps`
- [ ] Should see: api, worker, beat, redis, ollama, greenmail

### **Check Logs**

- [ ] API logs: `docker logs api`
- [ ] Worker logs: `docker logs worker`
- [ ] Beat logs: `docker logs beat`
- [ ] No errors in any logs

---

## ✅ Phase 4: Verification (10 minutes)

### **Test 1: API Health**

```bash
curl http://localhost:8000/health
```

- [ ] Returns `{"status": "ok", "agent_running": false}`

### **Test 2: Agent Status**

```bash
curl http://localhost:8000/agent/status
```

- [ ] Returns JSON with agent config
- [ ] Shows `"is_running": false`
- [ ] Shows limits and statistics

### **Test 3: Dashboard**

- [ ] Open `http://localhost:8000` in browser
- [ ] See agent control panel at top
- [ ] Status indicator shows red (stopped)
- [ ] Buttons: Start, Stop, Pause, Run Now
- [ ] Metrics show: 0/50 daily, 0/10 hourly
- [ ] Lead statistics display correctly

### **Test 4: Database**

```bash
sqlite3 data/data.db "SELECT COUNT(*) FROM leads WHERE agent_enabled = 1;"
```

- [ ] Returns count of agent-enabled leads
- [ ] Should match your imported leads

---

## 🚀 Phase 5: First Run (15 minutes)

### **Test Run (Safe)**

1. **Via Dashboard:**
   - [ ] Open `http://localhost:8000`
   - [ ] Click **Start** button
   - [ ] Confirm dialog
   - [ ] Status turns green: "Agent Running"

2. **Verify Activity:**
   - [ ] Watch worker logs: `docker logs worker -f`
   - [ ] Should see: "Agent cycle starting..."
   - [ ] Should see: "Decision engine..."
   - [ ] Should see decisions being made

3. **Check Agent Logs:**
   - [ ] Click "Agent Logs" tab in dashboard
   - [ ] See actions listed
   - [ ] Each entry shows: time, action, lead, result

### **Manual Cycle Test**

```bash
curl -X POST http://localhost:8000/agent/run-now
```

- [ ] Returns: `{"success": true, "results": {...}}`
- [ ] Shows `emails_queued`, `leads_skipped`, `errors`

### **Monitor First Email**

- [ ] Check GreenMail UI: `http://localhost:8080`
- [ ] Should see queued/sent emails
- [ ] Verify email content looks correct

---

## 🧪 Phase 6: Testing (20 minutes)

### **Test Scenarios**

1. **Test with YOUR email:**
   ```bash
   # Add yourself as test lead
   curl -X POST http://localhost:8000/leads/ \
     -H "Content-Type: application/json" \
     -d '{
       "email": "your@email.com",
       "first_name": "Test",
       "company": "Test Co",
       "industry": "Glassworks"
     }'
   
   # Run agent cycle
   curl -X POST http://localhost:8000/agent/run-now
   
   # Check your email (or GreenMail UI)
   ```

   - [ ] Email received
   - [ ] Content looks professional
   - [ ] No placeholder text

2. **Test Rate Limiting:**
   ```bash
   # Check limits
   curl http://localhost:8000/agent/status | grep -A 5 "limits"
   ```
   
   - [ ] Shows correct daily limit (50)
   - [ ] Shows correct hourly limit (10)
   - [ ] Counter increments after send

3. **Test Business Hours:**
   
   - [ ] If outside business hours, agent should skip
   - [ ] Check logs for: "Outside business hours"
   - [ ] Or disable temporarily to test

4. **Test Pause/Resume:**
   ```bash
   # Pause
   curl -X POST http://localhost:8000/agent/pause
   
   # Try to run
   curl -X POST http://localhost:8000/agent/run-now
   # Should return: "Agent is paused"
   
   # Resume
   curl -X POST http://localhost:8000/agent/resume
   ```
   
   - [ ] Pause works
   - [ ] Resume works
   - [ ] Dashboard reflects status

5. **Test Stop:**
   ```bash
   curl -X POST http://localhost:8000/agent/stop
   ```
   
   - [ ] Agent stops
   - [ ] Dashboard shows stopped
   - [ ] No more cycles run

---

## 📊 Phase 7: Monitoring (Ongoing)

### **Dashboard Monitoring**

Daily checks:

- [ ] Agent status (green = running)
- [ ] Emails sent today vs limit
- [ ] Success rate
- [ ] Error count
- [ ] Last run timestamp

### **Log Monitoring**

```bash
# Watch agent activity
docker logs worker -f | grep "Agent cycle"

# Watch for errors
docker logs worker -f | grep "ERROR"

# Watch decisions
docker logs worker -f | grep "Decision engine"
```

### **Database Checks**

```bash
# Lead status breakdown
sqlite3 data/data.db "SELECT status, COUNT(*) FROM leads GROUP BY status;"

# Agent-enabled leads
sqlite3 data/data.db "SELECT COUNT(*) FROM leads WHERE agent_enabled = 1;"

# Follow-up counts
sqlite3 data/data.db "SELECT follow_up_count, COUNT(*) FROM leads GROUP BY follow_up_count;"
```

---

## 🎯 Phase 8: Production Readiness (Optional)

### **Switch to Real SMTP**

- [ ] Update `.env` with production SMTP
- [ ] Test sending to real email
- [ ] Verify deliverability
- [ ] Check spam scores

### **Tune Agent Settings**

- [ ] Adjust daily limits based on ESP limits
- [ ] Fine-tune business hours
- [ ] Adjust follow-up delays
- [ ] Set appropriate max follow-ups

### **Scale Up**

- [ ] Import full lead list
- [ ] Monitor first 100 emails
- [ ] Gradually increase limits
- [ ] Track reply rates

---

## 🐛 Troubleshooting Guide

### **Agent Won't Start**

Check:
1. [ ] Agent config exists in database
2. [ ] No errors in API logs
3. [ ] Redis is running: `docker ps | grep redis`
4. [ ] Beat service is running: `docker ps | grep beat`

Fix:
```bash
# Restart services
docker-compose restart

# Check status
curl http://localhost:8000/agent/status
```

### **No Emails Being Sent**

Check:
1. [ ] Agent is running (not paused)
2. [ ] Within business hours
3. [ ] Haven't hit rate limits
4. [ ] Leads exist with `agent_enabled=1`
5. [ ] Ollama is responding

Fix:
```bash
# Check eligible leads
sqlite3 data/data.db "SELECT COUNT(*) FROM leads WHERE agent_enabled = 1 AND agent_paused = 0 AND status = 'new';"

# Test Ollama
curl http://localhost:11434/api/generate -d '{"model":"llama3","prompt":"test"}'

# Disable business hours temporarily
curl -X PATCH http://localhost:8000/agent/config \
  -d '{"respect_business_hours": false}'
```

### **Ollama Timeouts**

Already fixed in updated `ollama_service.py`:
- [ ] Timeout increased to 180s
- [ ] Model warm-up on startup
- [ ] Response length limited

### **Database Locked**

```bash
# Stop all services
docker-compose down

# Wait 5 seconds
sleep 5

# Restart
docker-compose up -d
```

---

## 📈 Success Metrics

After 24 hours of running:

- [ ] Agent has run multiple cycles
- [ ] Emails are being sent automatically
- [ ] Rate limits are respected
- [ ] No critical errors
- [ ] Agent logs show activity
- [ ] Lead statuses are updating
- [ ] Follow-ups are scheduled correctly

After 1 week:

- [ ] Multiple follow-ups sent successfully
- [ ] Replies are being detected (if IMAP working)
- [ ] Error rate < 5%
- [ ] No leads stuck in error state
- [ ] Business hours respected
- [ ] Daily limits never exceeded

---

## 📞 Getting Help

If stuck:

1. **Check logs first:**
   ```bash
   docker logs api
   docker logs worker
   docker logs beat
   ```

2. **Verify database:**
   ```bash
   sqlite3 data/data.db "SELECT * FROM agent_config;"
   ```

3. **Test API:**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/agent/status
   ```

4. **Review this checklist again**

5. **Read `AGENT_SETUP.md` for detailed troubleshooting**

---

## 🎉 You're Done!

When all checkboxes are ✅:

- **Agent is running autonomously**
- **Sending emails automatically**
- **Respecting all safety limits**
- **Logging all activity**
- **Ready for production!**

The system is now fully autonomous and will:
- Check for eligible leads every 5 minutes
- Send emails during business hours
- Follow up automatically after 3 days
- Stop after 3 attempts per lead
- Respect all rate limits
- Log every decision

**Welcome to autonomous email outreach! 🚀**