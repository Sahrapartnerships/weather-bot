#!/usr/bin/env python3
"""
Robofabio Weather Bot - Continuous Runner
Runs trading cycles every 30 minutes
"""

import time
import sys
import logging
from weather_bot import RobofabioCoordinator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ContinuousRunner')

def main():
    """Run bot continuously"""
    logger.info("🚀 Starting Robofabio Weather Bot - Continuous Mode")
    logger.info("⏱️ Trading every 30 minutes")
    
    coordinator = RobofabioCoordinator()
    
    while True:
        try:
            # Run trading cycle
            trades = coordinator.run_cycle()
            
            if trades and trades > 0:
                logger.info(f"✅ Executed {trades} trades")
            
            # Sleep for 30 minutes
            logger.info("😴 Sleeping for 30 minutes...")
            time.sleep(1800)  # 30 minutes
            
        except KeyboardInterrupt:
            logger.info("👋 Shutting down...")
            break
        except Exception as e:
            logger.error(f"❌ Error in cycle: {e}")
            logger.info("⏱️ Retrying in 5 minutes...")
            time.sleep(300)  # 5 minutes on error

if __name__ == '__main__':
    main()
