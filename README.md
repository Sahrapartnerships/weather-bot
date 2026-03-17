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

## 🚀 Schnell-Deploy (für Live Trading)

### Option 1: Fly.io - EMPFOHLEN ✅ (5 Minuten)

**Warum Fly.io:** Server in Wien, Österreich = **NICHT blockiert!**

```bash
# 1. Install Fly.io CLI
curl -L https://fly.io/install.sh | sh
export PATH="$HOME/.fly/bin:$PATH"

# 2. Login (öffnet Browser)
flyctl auth login

# 3. Clone Repository
git clone https://github.com/Sahrapartnerships/weather-bot.git
cd weather-bot

# 4. Setze Secrets (deine API Keys)
flyctl secrets set POLYMARKET_API_KEY="dein-api-key"
flyctl secrets set POLYMARKET_API_SECRET="dein-secret"
flyctl secrets set POLYMARKET_PASSPHRASE="dein-passphrase"
flyctl secrets set POLYGON_PRIVATE_KEY="dein-private-key"
flyctl secrets set WALLET_ADDRESS="deine-wallet-adresse"

# 5. Deploy auf Wien!
flyctl deploy --region vie

# 6. Logs ansehen
flyctl logs
```

**Fertig!** Bot läuft 24/7 auf Server in Wien (nicht geo-blockiert)

---

### Option 2: Einfaches Deploy-Script

```bash
git clone https://github.com/Sahrapartnerships/weather-bot.git
cd weather-bot
./deploy.sh fly
```

---

### Option 3: Docker (überall)

```bash
docker-compose up -d
```

## 📈 Performance Tracking

- SQLite Datenbank: `weather_bot.db`
- Trades, PnL, Win Rate
- Tägliche Reports

## ⚠️ Disclaimer

Trading Bots können Verluste verursachen. Paper Trading zuerst!
