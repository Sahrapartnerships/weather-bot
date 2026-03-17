#!/bin/bash
# ============================================================
# ROBOFABIO WEATHER BOT - LIVE TRADING DEPLOY
# Master Albert, this script deploys everything automatically
# ============================================================

set -e

BOT_DIR="/root/life/1_Projects/weather-bot"
REPO="https://github.com/Sahrapartnerships/weather-bot"

echo "🚀 ROBOFABIO WEATHER BOT - LIVE DEPLOY"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "$BOT_DIR/weather_bot.py" ]; then
    echo "❌ Bot not found at $BOT_DIR"
    exit 1
fi

cd "$BOT_DIR"

# ============================================================
# OPTION 1: FLY.IO (Österreich - NICHT BLOCKIERT!)
# ============================================================

deploy_fly() {
    echo ""
    echo "🌍 DEPLOY VIA FLY.IO (Vienna, Austria)"
    echo "--------------------------------------"
    
    # Check if flyctl is installed
    if ! command -v flyctl &> /dev/null; then
        echo "📥 Installing Fly.io CLI..."
        curl -L https://fly.io/install.sh | sh
        export PATH="$HOME/.fly/bin:$PATH"
    fi
    
    # Login (interactive - you need to run this manually)
    echo ""
    echo "🔐 Fly.io Login erforderlich:"
    echo "   Führe aus: flyctl auth login"
    echo "   Dann: ./deploy.sh fly"
    echo ""
    
    # Create app if not exists
    if ! flyctl status &> /dev/null; then
        echo "📦 Creating Fly.io app..."
        flyctl apps create weather-bot --org personal
    fi
    
    # Set secrets
    echo "🔑 Setting secrets..."
    flyctl secrets set POLYMARKET_API_KEY="$POLYMARKET_API_KEY"
    flyctl secrets set POLYMARKET_API_SECRET="$POLYMARKET_API_SECRET"
    flyctl secrets set POLYMARKET_PASSPHRASE="$POLYMARKET_PASSPHRASE"
    flyctl secrets set POLYGON_PRIVATE_KEY="$POLYGON_PRIVATE_KEY"
    flyctl secrets set WALLET_ADDRESS="$WALLET_ADDRESS"
    
    # Deploy
    echo "🚀 Deploying..."
    flyctl deploy --region vie  # Vienna, Austria
    
    echo ""
    echo "✅ DEPLOYED!"
    echo "   App: https://fly.io/apps/weather-bot"
    echo "   Logs: flyctl logs"
    echo "   Region: Vienna, Austria (NOT BLOCKED!)"
}

# ============================================================
# OPTION 2: MANUAL VPS (Any EU server not in block list)
# ============================================================

deploy_manual() {
    echo ""
    echo "🖥️ MANUAL VPS SETUP"
    echo "-------------------"
    echo ""
    echo "1. Rent a VPS in: Austria, Switzerland, Spain, or Ireland"
    echo "   Recommended: Hetzner (Finland/Austria), DigitalOcean (Frankfurt - check!)"
    echo ""
    echo "2. SSH into server and run:"
    echo ""
    echo "   git clone $REPO"
    echo "   cd weather-bot"
    echo "   pip3 install -r requirements.txt"
    echo "   export POLYMARKET_API_KEY='...'"
    echo "   export POLYGON_PRIVATE_KEY='...'"
    echo "   # ... other env vars"
    echo "   python3 run_continuous.py"
    echo ""
    echo "3. For 24/7 running, use screen or systemd:"
    echo "   screen -S weather-bot -dm python3 run_continuous.py"
    echo ""
}

# ============================================================
# OPTION 3: DOCKER (For any platform)
# ============================================================

create_docker() {
    echo ""
    echo "🐳 Creating Docker setup..."
    
    cat > Dockerfile << 'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run_continuous.py"]
DOCKERFILE

    cat > docker-compose.yml << 'COMPOSE'
version: '3.8'

services:
  weather-bot:
    build: .
    environment:
      - POLYMARKET_API_KEY=${POLYMARKET_API_KEY}
      - POLYMARKET_API_SECRET=${POLYMARKET_API_SECRET}
      - POLYMARKET_PASSPHRASE=${POLYMARKET_PASSPHRASE}
      - POLYGON_PRIVATE_KEY=${POLYGON_PRIVATE_KEY}
      - WALLET_ADDRESS=${WALLET_ADDRESS}
    restart: unless-stopped
COMPOSE

    echo "✅ Docker files created!"
    echo "   Build: docker-compose up -d"
}

# ============================================================
# MAIN MENU
# ============================================================

case "${1:-menu}" in
    fly)
        deploy_fly
        ;;
    manual)
        deploy_manual
        ;;
    docker)
        create_docker
        ;;
    *)
        echo ""
        echo "Wähle Deploy-Option:"
        echo ""
        echo "1) ./deploy.sh fly     - Fly.io (Vienna, Austria) - RECOMMENDED"
        echo "2) ./deploy.sh manual  - Manual VPS setup guide"
        echo "3) ./deploy.sh docker  - Create Docker files"
        echo ""
        echo "Empfohlen: Fly.io - Schnell, günstig, Vienna = NICHT blockiert!"
        echo ""
        ;;
esac
