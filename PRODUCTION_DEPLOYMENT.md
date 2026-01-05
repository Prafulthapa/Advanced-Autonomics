# 🚀 Production Deployment Guide

## Prerequisites

- [x] Gmail account with App Password generated
- [x] IMAP enabled in Gmail settings
- [x] Docker & Docker Compose installed
- [x] Server with at least 4GB RAM
- [x] Domain name (optional, for production URLs)

## Step 1: Environment Configuration

1. Copy `.env.example` to `.env`
2. Fill in all required values:
```bash
# CRITICAL: Update these
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
IMAP_USERNAME=your_email@gmail.com
IMAP_PASSWORD=your_app_password

# Adjust limits for production
DAILY_EMAIL_LIMIT=500    # Gmail free tier limit
HOURLY_EMAIL_LIMIT=50    # Avoid spam filters

# Set business hours
RESPECT_BUSINESS_HOURS=true
BUSINESS_HOURS_START=09:00
BUSINESS_HOURS_END=17:00
TIMEZONE=America/New_York
```

## Step 2: Initial Setup
```bash
# 1. Build containers
docker-compose build

# 2. Start services
docker-compose up -d

# 3. Check all containers are running
docker-compose ps

# 4. Check logs
docker-compose logs -f
```

## Step 3: Database Setup
```bash
# Run migration if needed
python create_email_queue_table.py

# Verify tables exist
docker-compose exec api python -c "
from app.database import SessionLocal, engine
from app.models import Lead
db = SessionLocal()
print('Tables:', engine.table_names())
print('Lead count:', db.query(Lead).count())
"
```

## Step 4: Import First Leads
```bash
# Via API
curl -X POST http://localhost:8000/import/csv \
  -F "file=@your_leads.csv"

# Via Dashboard
# Go to http://localhost:8000
# Click "Import" tab
# Upload CSV
```

## Step 5: Start Agent
```bash
# Via API
curl -X POST http://localhost:8000/agent/start

# Via Dashboard
# Click "Start Agent" button
```

## Step 6: Monitor

Access monitoring tools:

- **Main Dashboard**: http://localhost:8000
- **System Monitor**: http://localhost:8000/static/monitor.html
- **Health Check**: http://localhost:8000/health/full
- **Analytics**: http://localhost:8000/analytics/overview
- **API Docs**: http://localhost:8000/docs

## Step 7: Set Up Alerts (Optional)
```python
# In app/services/alert_service.py
# Configure email alerts or Slack webhooks
```

## Production Checklist

- [ ] ✅ All containers running
- [ ] ✅ Database tables created
- [ ] ✅ SMTP test passed
- [ ] ✅ IMAP test passed
- [ ] ✅ First lead imported
- [ ] ✅ Test email sent successfully
- [ ] ✅ Reply received and classified
- [ ] ✅ Agent running autonomously
- [ ] ✅ Monitoring dashboard accessible
- [ ] ✅ Rate limits configured
- [ ] ✅ Business hours respected
- [ ] ✅ Backup strategy in place

## Maintenance

### Daily
- Check dashboard for errors
- Review interested leads
- Monitor email queue status

### Weekly
- Export analytics CSV
- Review A/B test results
- Adjust rate limits if needed

### Monthly
- Clean up old logs (automatic)
- Review and update email templates
- Analyze conversion rates

## Troubleshooting

### Agent not sending emails
```bash
# Check status
curl http://localhost:8000/agent/status

# Check logs
docker-compose logs worker | tail -100

# Restart worker
docker-compose restart worker
```

### High error rate
```bash
# Check failed queue
curl http://localhost:8000/queue/failed

# Retry failed emails
curl -X POST http://localhost:8000/queue/retry/{id}
```

### IMAP authentication failed
```bash
# Test IMAP
python test_imap.py

# Generate new app password
# Update .env
# Restart containers
docker-compose restart
```

## Scaling

### For >1000 leads/day:
```yaml
# In docker-compose.yml
worker:
  deploy:
    replicas: 3  # Multiple workers

# Increase limits in .env
DAILY_EMAIL_LIMIT=1000
HOURLY_EMAIL_LIMIT=100
```

## Support

- Logs: `docker-compose logs -f`
- Health: `curl http://localhost:8000/health/full`
- Stats: `curl http://localhost:8000/analytics/overview`