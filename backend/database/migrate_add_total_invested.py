#!/usr/bin/env python3
"""
Migration script to add total_invested column to strategies table
Run this after updating the Strategy model
"""

import sqlite3
import os
from pathlib import Path

def add_total_invested_column():
    # Get the database path
    db_path = Path(__file__).parent.parent / "divetrader.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(strategies);")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'total_invested' in columns:
            print("total_invested column already exists")
            return
        
        # Add the new column
        cursor.execute("ALTER TABLE strategies ADD COLUMN total_invested REAL DEFAULT 0.0;")
        
        # Calculate initial values based on existing positions
        cursor.execute("""
            SELECT s.id, s.name, COALESCE(SUM(p.quantity * p.avg_price), 0) as invested
            FROM strategies s
            LEFT JOIN positions p ON s.id = p.strategy_id
            GROUP BY s.id, s.name
        """)
        
        strategies = cursor.fetchall()
        
        # Update each strategy with calculated invested amount
        for strategy_id, name, invested in strategies:
            cursor.execute(
                "UPDATE strategies SET total_invested = ? WHERE id = ?",
                (invested, strategy_id)
            )
            print(f"Updated strategy '{name}' with total_invested: ${invested:.2f}")
        
        # Commit changes
        conn.commit()
        print(f"Successfully added total_invested column and updated {len(strategies)} strategies")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_total_invested_column()