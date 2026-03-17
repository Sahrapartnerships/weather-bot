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

## 🚀 Deploy

### Option 1: Railway (EU-Ireland)
```bash
railway login
railway link
railway up
```

### Option 2: GitHub Actions (NUR für nicht-US Regionen!)
- Workflow läuft alle 30 Minuten
- Nutzt Secrets aus GitHub

## 📈 Performance Tracking

- SQLite Datenbank: `weather_bot.db`
- Trades, PnL, Win Rate
- Tägliche Reports

## ⚠️ Disclaimer

Trading Bots können Verluste verursachen. Paper Trading zuerst!
