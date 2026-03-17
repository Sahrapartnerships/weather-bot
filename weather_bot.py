#!/usr/bin/env python3
"""
Robofio Weather Trading Bot v1.0
Multi-Agent Swarm for Polymarket Weather Markets
- Agent A: Market Scout (find weather markets)
- Agent B: Weather Oracle (NOAA data + probability calc)
- Agent C: Edge Calculator (model vs market price)
- Agent D: Risk Guardian (limits & checks)
- Agent E: Trade Executor (CLOB orders)
- Robofabio: Coordinator & Self-Improvement
"""

import os
import sys
import json
import time
import sqlite3
import logging
import requests
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from web3 import Web3

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('WeatherBot')

# Config
DB_PATH = 'weather_bot.db'
NOAA_API = "https://api.weather.gov"
POLYMARKET_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"
GEOBLOCK_API = "https://polymarket.com/api/geoblock"

# Risk Limits
MAX_POSITION_SIZE = 50.0  # USDC
MAX_DAILY_LOSS = 200.0
MIN_EDGE = 0.10  # 10% edge required
CONFIDENCE_THRESHOLD = 0.60

# API Keys from env
POLY_API_KEY = os.getenv('POLYMARKET_API_KEY', '')
POLY_API_SECRET = os.getenv('POLYMARKET_API_SECRET', '')
POLY_PASSPHRASE = os.getenv('POLYMARKET_PASSPHRASE', '')
PRIVATE_KEY = os.getenv('POLYGON_PRIVATE_KEY', '')
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS', '')

class Database:
    """Agent: Data Persistence"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                market_id TEXT,
                market_question TEXT,
                side TEXT,
                size REAL,
                price REAL,
                model_prob REAL,
                market_prob REAL,
                edge REAL,
                order_id TEXT,
                status TEXT,
                pnl REAL,
                error TEXT
            )
        ''')
        
        # Weather data cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT,
                forecast_time TIMESTAMP,
                temperature REAL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Performance tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE,
                trades_count INTEGER,
                win_count INTEGER,
                loss_count INTEGER,
                total_pnl REAL,
                volume REAL
            )
        ''')
        
        # Bot state
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_trade(self, trade_data: Dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trades (market_id, market_question, side, size, price, 
                              model_prob, market_prob, edge, order_id, status, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data.get('market_id'),
            trade_data.get('market_question'),
            trade_data.get('side'),
            trade_data.get('size'),
            trade_data.get('price'),
            trade_data.get('model_prob'),
            trade_data.get('market_prob'),
            trade_data.get('edge'),
            trade_data.get('order_id'),
            trade_data.get('status'),
            trade_data.get('error')
        ))
        conn.commit()
        conn.close()
    
    def get_today_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT COUNT(*), SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END),
                   SUM(pnl), SUM(size)
            FROM trades 
            WHERE DATE(timestamp) = ? AND status = 'executed'
        ''', (today,))
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'trades': row[0] or 0,
            'wins': row[1] or 0,
            'losses': row[2] or 0,
            'pnl': row[3] or 0,
            'volume': row[4] or 0
        }

class GeoblockChecker:
    """Agent: Check if we can trade from current location"""
    
    @staticmethod
    def check() -> Dict:
        """Check if current IP is blocked"""
        try:
            resp = requests.get(GEOBLOCK_API, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"🌍 Geo-Check: {data['country']} - Blocked: {data['blocked']}")
                return data
        except Exception as e:
            logger.error(f"Geo-check failed: {e}")
        
        return {'blocked': True, 'country': 'Unknown', 'error': 'Check failed'}

class MarketScout:
    """Agent A: Find weather markets on Polymarket"""
    
    WEATHER_KEYWORDS = ['temperature', 'temp', 'weather', 'rain', 'snow', 'sunny', 'storm', 
                       'celsius', 'fahrenheit', 'degrees', 'hot', 'cold', 'freezing']
    
    def scan_weather_markets(self, limit: int = 50) -> List[Dict]:
        """Scan for weather-related markets"""
        try:
            resp = requests.get(
                f'{POLYMARKET_API}/markets',
                params={'closed': 'false', 'archived': 'false', 'limit': limit},
                timeout=10
            )
            
            if resp.status_code != 200:
                logger.error(f"Markets API error: {resp.status_code}")
                return []
            
            markets = resp.json()
            weather_markets = []
            
            for market in markets:
                question = market.get('question', '').lower()
                
                # Check if weather-related
                if any(keyword in question for keyword in self.WEATHER_KEYWORDS):
                    # Parse prices
                    prices_raw = market.get('outcomePrices', '[]')
                    if isinstance(prices_raw, str):
                        try:
                            prices = json.loads(prices_raw)
                        except:
                            prices = []
                    else:
                        prices = prices_raw
                    
                    if len(prices) >= 2:
                        market['parsed_prices'] = {
                            'yes': float(prices[0]),
                            'no': float(prices[1])
                        }
                        weather_markets.append(market)
            
            logger.info(f"🌤️ Agent A: Found {len(weather_markets)} weather markets")
            return weather_markets
            
        except Exception as e:
            logger.error(f"Market scan failed: {e}")
            return []
    
    def extract_location(self, question: str) -> Optional[Tuple[str, float, float]]:
        """Extract location and coordinates from market question"""
        # Location mapping
        locations = {
            'new york': ('New York', 40.7128, -74.0060),
            'nyc': ('New York', 40.7128, -74.0060),
            'los angeles': ('Los Angeles', 34.0522, -118.2437),
            'la': ('Los Angeles', 34.0522, -118.2437),
            'chicago': ('Chicago', 41.8781, -87.6298),
            'london': ('London', 51.5074, -0.1278),
            'paris': ('Paris', 48.8566, 2.3522),
            'tokyo': ('Tokyo', 35.6762, 139.6503),
            'sydney': ('Sydney', -33.8688, 151.2093),
            'tel aviv': ('Tel Aviv', 32.0853, 34.7818),
        }
        
        question_lower = question.lower()
        for key, data in locations.items():
            if key in question_lower:
                return data
        
        return None

class WeatherOracle:
    """Agent B: Get NOAA data and calculate probabilities"""
    
    def get_forecast(self, lat: float, lon: float) -> Optional[Dict]:
        """Get hourly forecast from NOAA"""
        try:
            # Get grid endpoint
            point_resp = requests.get(
                f'{NOAA_API}/points/{lat},{lon}',
                timeout=10,
                headers={'User-Agent': 'WeatherBot/1.0'}
            )
            
            if point_resp.status_code != 200:
                logger.warning(f"NOAA point error: {point_resp.status_code}")
                return None
            
            point_data = point_resp.json()
            forecast_url = point_data['properties']['forecastHourly']
            
            # Get forecast
            forecast_resp = requests.get(
                forecast_url,
                timeout=10,
                headers={'User-Agent': 'WeatherBot/1.0'}
            )
            
            if forecast_resp.status_code != 200:
                return None
            
            return forecast_resp.json()
            
        except Exception as e:
            logger.error(f"Weather fetch failed: {e}")
            return None
    
    def calculate_probability(self, threshold: float, forecast_temps: List[float], 
                             comparison: str = 'above') -> float:
        """Calculate probability using normal distribution"""
        if not forecast_temps:
            return 0.5
        
        mean_temp = sum(forecast_temps) / len(forecast_temps)
        
        # Standard deviation (conservative estimate)
        if len(forecast_temps) > 1:
            variance = sum((t - mean_temp) ** 2 for t in forecast_temps) / len(forecast_temps)
            std = max(math.sqrt(variance), 2.0)  # Min 2 degrees std
        else:
            std = 3.0  # Default uncertainty
        
        # Calculate z-score
        if comparison == 'above':
            z = (mean_temp - threshold) / std
        else:
            z = (threshold - mean_temp) / std
        
        # Convert to probability using error function
        prob = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        
        return max(0.05, min(0.95, prob))  # Bound between 5% and 95%
    
    def extract_threshold(self, question: str) -> Optional[Tuple[float, str]]:
        """Extract temperature threshold from question"""
        import re
        
        # Look for patterns like "70°F", "70 degrees", "above 70"
        patterns = [
            r'(\d+)\s*°?\s*[Ff]',
            r'(\d+)\s*degrees',
            r'above\s+(\d+)',
            r'over\s+(\d+)',
            r'below\s+(\d+)',
            r'under\s+(\d+)',
        ]
        
        question_lower = question.lower()
        
        for pattern in patterns:
            match = re.search(pattern, question_lower)
            if match:
                temp = float(match.group(1))
                
                # Determine comparison
                if 'below' in question_lower or 'under' in question_lower or 'colder' in question_lower:
                    return (temp, 'below')
                else:
                    return (temp, 'above')
        
        return None

class EdgeCalculator:
    """Agent C: Calculate edge between model and market"""
    
    @staticmethod
    def calculate_edge(model_prob: float, market_prob: float) -> float:
        """Calculate edge (model - market)"""
        return model_prob - market_prob
    
    @staticmethod
    def should_trade(edge: float, model_prob: float, market_prob: float) -> bool:
        """Determine if we should trade"""
        # Need minimum edge
        if abs(edge) < MIN_EDGE:
            return False
        
        # Model needs to be confident enough
        if model_prob < 0.5 and market_prob < 0.5:
            # Both think NO - no trade
            return False
        
        if model_prob > 0.5 and market_prob > 0.5:
            # Both think YES - check if we have edge
            return edge > MIN_EDGE
        
        # Disagreement - trade if edge is significant
        return abs(edge) > MIN_EDGE + 0.05

class RiskGuardian:
    """Agent D: Risk management and limits"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def check_limits(self, trade_size: float) -> Tuple[bool, str]:
        """Check if trade is within limits"""
        stats = self.db.get_today_stats()
        
        # Check position size
        if trade_size > MAX_POSITION_SIZE:
            return False, f"Position size ${trade_size} exceeds max ${MAX_POSITION_SIZE}"
        
        # Check daily loss limit
        if stats['pnl'] < -MAX_DAILY_LOSS:
            return False, f"Daily loss ${stats['pnl']} exceeds limit ${MAX_DAILY_LOSS}"
        
        # Max trades per day
        if stats['trades'] >= 20:
            return False, "Max 20 trades per day reached"
        
        return True, "OK"
    
    def get_position_size(self, edge: float, confidence: float) -> float:
        """Calculate position size based on edge and confidence"""
        base_size = 10.0  # Base $10
        
        # Scale by edge (more edge = bigger position)
        edge_multiplier = min(abs(edge) * 5, 2.0)  # Max 2x
        
        # Scale by confidence
        confidence_multiplier = confidence
        
        size = base_size * edge_multiplier * confidence_multiplier
        return min(size, MAX_POSITION_SIZE)

class TradeExecutor:
    """Agent E: Execute trades on CLOB"""
    
    def __init__(self):
        self.simulation = not all([POLY_API_KEY, PRIVATE_KEY])
        if self.simulation:
            logger.warning("⚠️ Running in SIMULATION mode - no real trades")
    
    def execute_trade(self, market_id: str, side: str, size: float, 
                     price: float, market_question: str) -> Dict:
        """Execute trade on Polymarket CLOB"""
        
        if self.simulation:
            logger.info(f"[SIMULATION] {side} ${size} @ {price} - {market_question[:40]}")
            return {
                'success': True,
                'order_id': f'SIM_{int(time.time())}',
                'status': 'simulated'
            }
        
        try:
            # Check geo-block first
            geo = GeoblockChecker.check()
            if geo.get('blocked'):
                return {
                    'success': False,
                    'error': f"Geo-blocked: {geo.get('country')}"
                }
            
            # Place order via CLOB API
            # NOTE: Full implementation requires py-clob-client with proper auth
            logger.info(f"🚀 Executing: {side} ${size} @ {price}")
            
            # TODO: Implement actual CLOB order placement
            # For now, log the attempt
            return {
                'success': False,
                'error': 'Live trading requires py-clob-client setup'
            }
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return {'success': False, 'error': str(e)}

class RobofabioCoordinator:
    """
    Robofabio: Coordinator & Self-Improvement System
    Orchestrates all agents and learns from results
    """
    
    def __init__(self):
        self.db = Database()
        self.scout = MarketScout()
        self.oracle = WeatherOracle()
        self.edge_calc = EdgeCalculator()
        self.risk = RiskGuardian(self.db)
        self.executor = TradeExecutor()
    
    def run_cycle(self):
        """Run one full trading cycle"""
        logger.info("="*60)
        logger.info("🤖 ROBOFABIO WEATHER BOT - CYCLE START")
        logger.info("="*60)
        
        # Step 1: Check geo-block
        geo = GeoblockChecker.check()
        if geo.get('blocked'):
            logger.error(f"❌ Cannot trade from {geo.get('country')}")
            return
        
        # Step 2: Find weather markets
        markets = self.scout.scan_weather_markets()
        if not markets:
            logger.info("No weather markets found")
            return
        
        trades_executed = 0
        
        for market in markets[:5]:  # Check top 5
            question = market.get('question', '')
            market_id = market.get('conditionId') or market.get('slug')
            prices = market.get('parsed_prices', {})
            
            logger.info(f"\n📊 Analyzing: {question[:60]}...")
            
            # Step 3: Extract location
            location = self.scout.extract_location(question)
            if not location:
                logger.info("   No location found")
                continue
            
            name, lat, lon = location
            logger.info(f"   Location: {name} ({lat}, {lon})")
            
            # Step 4: Get weather forecast
            forecast = self.oracle.get_forecast(lat, lon)
            if not forecast:
                logger.info("   No forecast available")
                continue
            
            periods = forecast['properties']['periods'][:24]  # Next 24 hours
            temps = [p['temperature'] for p in periods]
            
            # Step 5: Extract threshold
            threshold_data = self.oracle.extract_threshold(question)
            if not threshold_data:
                logger.info("   No temperature threshold found")
                continue
            
            threshold, comparison = threshold_data
            logger.info(f"   Threshold: {threshold}°F ({comparison})")
            
            # Step 6: Calculate model probability
            model_prob = self.oracle.calculate_probability(threshold, temps, comparison)
            logger.info(f"   Model prob: {model_prob:.2%}")
            
            # Step 7: Get market probability
            market_prob = prices.get('yes', 0.5)
            logger.info(f"   Market prob: {market_prob:.2%}")
            
            # Step 8: Calculate edge
            edge = self.edge_calc.calculate_edge(model_prob, market_prob)
            logger.info(f"   Edge: {edge:+.2%}")
            
            # Step 9: Check if we should trade
            if not self.edge_calc.should_trade(edge, model_prob, market_prob):
                logger.info("   No trade - insufficient edge")
                continue
            
            # Step 10: Determine side
            if model_prob > market_prob:
                side = 'BUY'  # Buy YES
                trade_prob = market_prob
            else:
                side = 'SELL'  # Buy NO
                trade_prob = 1 - market_prob
            
            # Step 11: Calculate position size
            confidence = max(model_prob, 1 - model_prob)
            size = self.risk.get_position_size(edge, confidence)
            
            # Step 12: Check risk limits
            can_trade, reason = self.risk.check_limits(size)
            if not can_trade:
                logger.warning(f"   Risk check failed: {reason}")
                continue
            
            # Step 13: Execute trade
            logger.info(f"   🎯 EXECUTING: {side} ${size:.2f}")
            
            result = self.executor.execute_trade(
                market_id=market_id,
                side=side,
                size=size,
                price=trade_prob,
                market_question=question
            )
            
            # Log trade
            trade_data = {
                'market_id': market_id,
                'market_question': question,
                'side': side,
                'size': size,
                'price': trade_prob,
                'model_prob': model_prob,
                'market_prob': market_prob,
                'edge': edge,
                'order_id': result.get('order_id'),
                'status': 'executed' if result['success'] else 'failed',
                'error': result.get('error')
            }
            self.db.log_trade(trade_data)
            
            if result['success']:
                trades_executed += 1
                logger.info(f"   ✅ Trade executed: {result['order_id']}")
            else:
                logger.error(f"   ❌ Trade failed: {result.get('error')}")
        
        # Summary
        stats = self.db.get_today_stats()
        logger.info("\n" + "="*60)
        logger.info("📊 CYCLE SUMMARY")
        logger.info(f"   Trades executed: {trades_executed}")
        logger.info(f"   Today's trades: {stats['trades']}")
        logger.info(f"   Today's PnL: ${stats['pnl']:.2f}")
        logger.info("="*60)
        
        return trades_executed

def main():
    """Main entry point"""
    coordinator = RobofabioCoordinator()
    
    # Run single cycle
    coordinator.run_cycle()

if __name__ == '__main__':
    main()
