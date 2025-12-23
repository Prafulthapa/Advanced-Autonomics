#!/bin/bash

# Advanced Autonomics - AI Agent Setup Script
# Run this to quickly set up the agent

set -e  # Exit on error

echo "🤖 Advanced Autonomics AI Agent Setup"
echo "======================================"
echo ""

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Step 1: Backup database
echo "📦 Step 1: Backing up database..."
if [ -f "data/data.db" ]; then
    BACKUP_NAME="data.db.backup.$(date +%Y%m%d_%H%M%S)"
    cp data/data.db "data/$BACKUP_NAME"
    echo "✅ Database backed up to: data/$BACKUP_NAME"
else
    echo "⚠️  No existing database found (fresh install)"
fi

# Step 2: Create new directories
echo ""
echo "📁 Step 2: Creating directories..."
mkdir -p app/agent
mkdir -p app/utils
mkdir -p migrations
echo "✅ Directories created"

# Step 3: Check for required files
echo ""
echo "📄 Step 3: Checking required files..."
REQUIRED_FILES=(
    "app/models/agent_config.py"
    "app/models/agent_action_log.py"
    "app/agent/agent_runner.py"
    "app/agent/decision_engine.py"
    "app/agent/safety_controller.py"
    "app/agent/state_manager.py"
    "app/utils/time_utils.py"
    "app/utils/rate_limiter.py"
    "app/routes/agent_routes.py"
    "app/worker/agent_tasks.py"
    "app/config.py"
    "agent_config.yaml"
    "run_migration.py"
)

MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo ""
    echo "❌ Error: $MISSING_FILES required files are missing"
    echo "Please copy all files from the artifacts first"
    exit 1
fi

echo "✅ All required files present"

# Step 4: Run database migration
echo ""
echo "🗄️  Step 4: Running database migration..."
if python run_migration.py; then
    echo "✅ Database migration completed"
else
    echo "❌ Migration failed - check errors above"
    exit 1
fi

# Step 5: Verify migration
echo ""
echo "🔍 Step 5: Verifying migration..."
if sqlite3 data/data.db "SELECT COUNT(*) FROM agent_config;" > /dev/null 2>&1; then
    echo "✅ Agent config table created"
else
    echo "❌ Agent config table not found"
    exit 1
fi

# Step 6: Install dependencies
echo ""
echo "📦 Step 6: Installing Python dependencies..."
if pip install -r requirements.txt --quiet; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Step 7: Stop old containers
echo ""
echo "🛑 Step 7: Stopping old Docker containers..."
docker-compose down
echo "✅ Containers stopped"

# Step 8: Rebuild containers
echo ""
echo "🔨 Step 8: Building Docker images..."
docker-compose build --quiet
echo "✅ Images built"

# Step 9: Start services
echo ""
echo "🚀 Step 9: Starting services..."
docker-compose up -d
echo "✅ Services started"

# Step 10: Wait for services
echo ""
echo "⏳ Step 10: Waiting for services to be ready..."
sleep 10

# Check API health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is running"
else
    echo "⚠️  API not responding yet (may need more time)"
fi

# Step 11: Check agent status
echo ""
echo "🤖 Step 11: Checking agent status..."
if curl -s http://localhost:8000/agent/status > /dev/null 2>&1; then
    echo "✅ Agent API is responding"
else
    echo "⚠️  Agent API not responding yet"
fi

# Final summary
echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "🌐 Dashboard: http://localhost:8000"
echo "📚 API Docs:  http://localhost:8000/docs"
echo "🤖 Agent API: http://localhost:8000/agent/status"
echo ""
echo "Next steps:"
echo "1. Open dashboard: http://localhost:8000"
echo "2. Check agent status in control panel"
echo "3. Click 'Start' to begin autonomous operation"
echo "4. Monitor logs: docker logs worker -f"
echo ""
echo "Read AGENT_SETUP.md for detailed documentation"
echo ""