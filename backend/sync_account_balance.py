#!/usr/bin/env python3
"""
Sync strategy capital with actual Alpaca account balance
This script should be run periodically to keep strategies aligned with real account balance
"""

import os
import sys
import sqlite3
import logging
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_alpaca_account_balance():
    """Get current Alpaca account balance"""
    try:
        trading_client = TradingClient(
            api_key=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY"),
            paper=True
        )
        
        account = trading_client.get_account()
        return {
            "equity": float(account.equity),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power)
        }
    except Exception as e:
        logger.error(f"Error getting Alpaca account info: {e}")
        return None

def sync_strategy_capitals():
    """Sync all strategy capitals with account balance"""
    try:
        # Get Alpaca account balance
        account_info = get_alpaca_account_balance()
        if not account_info:
            logger.error("Could not get Alpaca account info")
            return False
        
        account_equity = account_info["equity"]
        logger.info(f"Current Alpaca account equity: ${account_equity:.2f}")
        
        # Connect to database
        conn = sqlite3.connect('divetrader.db')
        cursor = conn.cursor()
        
        # Get all strategies
        cursor.execute("SELECT id, name, strategy_type, initial_capital, current_capital FROM strategies")
        strategies = cursor.fetchall()
        
        if not strategies:
            logger.info("No strategies found")
            return True
        
        # Distribute account equity among strategies proportionally
        total_current_capital = sum(strategy[4] for strategy in strategies)  # current_capital
        
        for strategy in strategies:
            strategy_id, name, strategy_type, initial_capital, current_capital = strategy
            
            # Calculate proportional allocation
            if total_current_capital > 0:
                proportion = current_capital / total_current_capital
                new_capital = account_equity * proportion
            else:
                # Equal distribution if no current capital
                new_capital = account_equity / len(strategies)
            
            # Update strategy capital
            cursor.execute("""
                UPDATE strategies 
                SET initial_capital = ?, current_capital = ? 
                WHERE id = ?
            """, (new_capital, new_capital, strategy_id))
            
            logger.info(f"Updated {name} ({strategy_type}): ${current_capital:.2f} -> ${new_capital:.2f}")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Strategy capitals synced with Alpaca account")
        return True
        
    except Exception as e:
        logger.error(f"Error syncing strategy capitals: {e}")
        return False

def main():
    """Main function"""
    print("🔄 Syncing strategy capitals with Alpaca account...")
    print("=" * 50)
    
    success = sync_strategy_capitals()
    
    if success:
        print("🎉 Sync completed successfully!")
        return 0
    else:
        print("❌ Sync failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())