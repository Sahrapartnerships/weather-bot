#!/bin/bash
# Deploy script for Weather Bot

export RAILWAY_TOKEN=d9c5b6c6-e0ca-44ff-adc3-b64a75cbd24a

cd /root/life/1_Projects/weather-bot

# Check if railway CLI is logged in
if ! railway whoami > /dev/null 2>&1; then
    echo "Logging into Railway..."
    echo "$RAILWAY_TOKEN" | railway login --token-stdin
fi

# Initialize project if not exists
if [ ! -f .railway/config.json ]; then
    echo "Creating Railway project..."
    railway init --name weather-bot
fi

# Set environment variables
echo "Setting environment variables..."
railway variables --set "POLYMARKET_API_KEY=${POLYMARKET_API_KEY}"
railway variables --set "POLYMARKET_API_SECRET=${POLYMARKET_API_SECRET}"
railway variables --set "POLYMARKET_PASSPHRASE=${POLYMARKET_PASSPHRASE}"
railway variables --set "POLYGON_PRIVATE_KEY=${POLYGON_PRIVATE_KEY}"
railway variables --set "WALLET_ADDRESS=${WALLET_ADDRESS}"

# Deploy
echo "Deploying..."
railway up

echo "Done! Check: railway logs"
