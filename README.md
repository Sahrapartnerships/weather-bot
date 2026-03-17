# 🤖 Robofabio Weather Trading Bot

Multi-Agent Trading System for Polymarket Weather Markets

## 🏗️ Architecture

### 5-Agent Swarm:
1. **Agent A - Market Scout**: Findet Wetter-Märkte auf Polymarket
2. **Agent B - Weather Oracle**: Holt NOAA-Daten, berechnet Wahrscheinlichkeiten
3. **Agent C - Edge Calculator**: Vergleicht Modell vs Marktpreis
4. **Agent D - Risk Guardian**: Limits, Positionsgrößen, Verlustkontrolle
5. **Agent E - Trade Executor**: Führt Trades auf CLOB aus

### 🤖 Robofabio (Coordinator)
- Koordiniert alle Agents
- Self-Improvement Loop
- Performance Tracking

## 🌍 Geo-Block Lösung

**WICHTIG:** Polymarket blockiert USA, Deutschland, UK, etc.

**Erlaubte Regionen für Deploy:**
- ✅ EU-West-1 (Ireland)
- ✅ EU-Central (Frankfurt) - **Aber nicht für DE Nutzer!**
- ✅ Asien (außer SG, TH, TW)
- ✅ Schweiz, Österreich, etc.

**GitHub Actions:** Läuft auf US-Servern → **BLOCKIERT!**

**Lösungen:**
1. Railway EU-Region (Ireland)
2. Hetzner (Deutschland Server, aber nicht für DE Nutzer)
3. AWS EU-West-1 (Ireland)

## 📊 Trading Logik

```
Marktpreis YES = 0.40 (40%)
NOAA Modell = 0.55 (55%)
Edge = +0.15 (15%)
→ TRADE BUY YES!
```

## 🛠️ Setup

```bash
pip install -r requirements.txt
export POLYMARKET_API_KEY="..."
export POLYGON_PRIVATE_KEY="..."
python weather_bot.py
```

## 🚀 Deploy Optionen

### Option 1: Railway (EU-Ireland) - EMPFOHLEN ✅
**Warum:** Railway EU-Region ist nicht geo-blockiert!

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login (Browser)
railway login

# Link Projekt
cd weather-bot
railway init --name weather-bot

# Setze Environment Variables in Railway Dashboard:
# - POLYMARKET_API_KEY
# - POLYMARKET_API_SECRET
# - POLYMARKET_PASSPHRASE
# - POLYGON_PRIVATE_KEY
# - WALLET_ADDRESS

# Deploy
railway up

# Setze Cron Job (alle 30 Minuten)
railway add --cron "*/30 * * * *" --command "python weather_bot.py"
```

**Wichtig:** In Railway Dashboard → Settings → Region: **EU-West (Ireland)** wählen!

### Option 2: Hetzner / VPS (Europa)
```bash
# Auf EU-Server (nicht DE, nicht UK, nicht FR)
# z.B.: Schweiz, Österreich, Niederlande (außer NL), etc.

git clone https://github.com/Sahrapartnerships/weather-bot.git
cd weather-bot
pip install -r requirements.txt

# Environment setup
export POLYMARKET_API_KEY="..."
# ... andere Variablen

# Cron einrichten
crontab -e
# */30 * * * * cd /path/to/weather-bot && python weather_bot.py >> cron.log 2>&1
```

### Option 3: AWS EC2 (eu-west-1: Ireland)
- Instance in **eu-west-1** (Ireland) starten
- Nicht eu-west-2 (UK) - UK ist blockiert!

### Option 4: GitHub Actions (NICHT EMPFOHLEN) ❌
GitHub Actions läuft auf US-Servern → **BLOCKIERT!**
Nur verwenden wenn du einen Self-Hosted Runner in Europa hast.

## 📈 Performance Tracking

- SQLite Datenbank: `weather_bot.db`
- Trades, PnL, Win Rate
- Tägliche Reports

## ⚠️ Disclaimer

Trading Bots können Verluste verursachen. Paper Trading zuerst!
