#!/usr/bin/env python3

import sqlite3
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
import argparse
from db_helper import get_db_connection, DEFAULT_DB_PATH

def create_risk_tables(db_path=None):
    """Create tables for risk data if they don't exist"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Create risk metrics table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS risk_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        risk_type TEXT NOT NULL,
        value REAL NOT NULL,
        rwa REAL,
        trend TEXT,
        reporting_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create risk sources table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS risk_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        risk_metric_id INTEGER NOT NULL,
        source_name TEXT NOT NULL,
        contribution_pct REAL NOT NULL,
        FOREIGN KEY (risk_metric_id) REFERENCES risk_metrics (id)
    )
    ''')
    
    # Create risk thresholds table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS risk_thresholds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        risk_type TEXT NOT NULL,
        warning_threshold REAL NOT NULL,
        critical_threshold REAL NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create capital ratios table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS capital_ratios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ratio_type TEXT NOT NULL,
        value REAL NOT NULL,
        reporting_date DATE NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def generate_random_risk_data(num_days=90, db_path=None):
    """Generate random risk data for the past num_days"""
    # Risk types and their characteristics
    risk_types = {
        "credit_risk": {
            "initial_value": 8.7,
            "volatility": 0.5,
            "rwa_base": 245.3,
            "rwa_volatility": 10,
            "sources": ["Loan Portfolio", "Corporate Bonds", "Retail Mortgages", "Sovereign Debt", "Interbank Lending"]
        },
        "market_risk": {
            "initial_value": 3.2,
            "volatility": 0.3,
            "rwa_base": 98.6,
            "rwa_volatility": 8,
            "sources": ["Trading Book", "FX Positions", "Derivatives", "Commodity Risk", "Interest Rate Risk"]
        },
        "operational_risk": {
            "initial_value": 2.1,
            "volatility": 0.2,
            "rwa_base": 65.4,
            "rwa_volatility": 5,
            "sources": ["Process Errors", "System Failures", "External Events", "Legal Risk", "Employee Conduct"]
        },
        "liquidity_risk": {
            "initial_value": 112,
            "volatility": 5,
            "rwa_base": None,  # LCR doesn't have RWA
            "rwa_volatility": None,
            "sources": ["Deposit Base", "Wholesale Funding", "Liquid Assets", "Intraday Liquidity", "Cross-Currency Funding"]
        },
        "concentration_risk": {
            "initial_value": 14.3,
            "volatility": 1.0,
            "rwa_base": 54.7,
            "rwa_volatility": 7,
            "sources": ["Sector Exposure", "Geographic Concentration", "Single Names", "Connected Clients", "Product Concentration"]
        }
    }
    
    # Define thresholds for each risk type
    risk_thresholds = {
        "credit_risk": {"warning": 10.0, "critical": 12.0},
        "market_risk": {"warning": 4.5, "critical": 6.0},
        "operational_risk": {"warning": 3.0, "critical": 4.0},
        "liquidity_risk": {"warning": 105.0, "critical": 100.0},  # For LCR, lower is worse
        "concentration_risk": {"warning": 16.0, "critical": 20.0}
    }
    
    # Generate data
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM risk_sources")
    cursor.execute("DELETE FROM risk_metrics")
    cursor.execute("DELETE FROM risk_thresholds")
    cursor.execute("DELETE FROM capital_ratios")
    
    # Insert risk thresholds
    for risk_type, thresholds in risk_thresholds.items():
        cursor.execute(
            "INSERT INTO risk_thresholds (risk_type, warning_threshold, critical_threshold) VALUES (?, ?, ?)",
            (risk_type, thresholds["warning"], thresholds["critical"])
        )
    
    # Generate time series data
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=num_days)
    
    metrics_data = []
    sources_data = []
    capital_ratios_data = []
    
    # Initial capital ratio
    total_capital_ratio = 15.6
    
    for day in range(num_days + 1):
        current_date = start_date + timedelta(days=day)
        
        # Update capital ratio with some random walk
        total_capital_ratio += np.random.normal(0, 0.1)
        # Ensure it stays within realistic bounds
        total_capital_ratio = max(10.5, min(total_capital_ratio, 18.0))
        
        # Determine capital status
        if total_capital_ratio >= 14.0:
            status = "Compliant"
        elif total_capital_ratio >= 12.5:
            status = "Warning"
        else:
            status = "Non-Compliant"
        
        # Add capital ratio record
        capital_ratios_data.append({
            "ratio_type": "total_capital_ratio",
            "value": round(total_capital_ratio, 2),
            "reporting_date": current_date,
            "status": status
        })
        
        # Add tier1 capital ratio (always a bit lower than total)
        tier1_ratio = total_capital_ratio * 0.85 + np.random.normal(0, 0.1)
        if tier1_ratio >= 11.0:
            tier1_status = "Compliant"
        elif tier1_ratio >= 9.5:
            tier1_status = "Warning"
        else:
            tier1_status = "Non-Compliant"
        
        capital_ratios_data.append({
            "ratio_type": "tier1_capital_ratio",
            "value": round(tier1_ratio, 2),
            "reporting_date": current_date,
            "status": tier1_status
        })
        
        # Generate risk metrics for this day
        for risk_type, params in risk_types.items():
            # Apply random walk to the risk value
            if day == 0:
                # Start with initial value
                current_value = params["initial_value"]
            else:
                # Get previous value for this risk type
                for metric in metrics_data:
                    if metric["risk_type"] == risk_type and metric["reporting_date"] == current_date - timedelta(days=1):
                        prev_value = metric["value"]
                        break
                
                # Apply random walk with mean reversion
                mean_reversion = 0.3  # Strength of mean reversion
                random_shock = np.random.normal(0, params["volatility"])
                mean_reversion_term = mean_reversion * (params["initial_value"] - prev_value)
                current_value = prev_value + mean_reversion_term + random_shock
            
            # Ensure value doesn't go negative (except for liquidity risk which can't go below 70)
            if risk_type == "liquidity_risk":
                current_value = max(70, current_value)
            else:
                current_value = max(0.5, current_value)
            
            # Calculate RWA if applicable
            if params["rwa_base"] is not None:
                rwa = params["rwa_base"] * (current_value / params["initial_value"]) + np.random.normal(0, params["rwa_volatility"])
                rwa = max(10, rwa)  # Ensure RWA doesn't go too low
            else:
                rwa = None
            
            # Determine trend based on last 7 days
            trend = "stable"  # Default
            if day >= 7:
                # Get value from 7 days ago
                for metric in metrics_data:
                    if metric["risk_type"] == risk_type and metric["reporting_date"] == current_date - timedelta(days=7):
                        week_ago_value = metric["value"]
                        pct_change = ((current_value - week_ago_value) / week_ago_value) * 100
                        
                        if risk_type == "liquidity_risk":
                            # For liquidity risk, higher is better
                            if pct_change > 2:
                                trend = "increasing"
                            elif pct_change < -2:
                                trend = "decreasing"
                        else:
                            # For other risks, lower is better
                            if pct_change > 2:
                                trend = "increasing"
                            elif pct_change < -2:
                                trend = "decreasing"
                        break
            
            # Add to metrics data list
            metrics_data.append({
                "risk_type": risk_type,
                "value": round(current_value, 2),
                "rwa": round(rwa, 2) if rwa is not None else None,
                "trend": trend,
                "reporting_date": current_date
            })
    
    # Insert metrics data
    for metric in metrics_data:
        cursor.execute(
            "INSERT INTO risk_metrics (risk_type, value, rwa, trend, reporting_date) VALUES (?, ?, ?, ?, ?)",
            (metric["risk_type"], metric["value"], metric["rwa"], metric["trend"], metric["reporting_date"])
        )
        metric_id = cursor.lastrowid
        
        # Generate random source contributions that sum to 100%
        sources = risk_types[metric["risk_type"]]["sources"]
        num_sources = len(sources)
        
        # Random weights that sum to 1
        weights = np.random.dirichlet(np.ones(num_sources))
        
        for i, source in enumerate(sources):
            sources_data.append({
                "risk_metric_id": metric_id,
                "source_name": source,
                "contribution_pct": round(weights[i] * 100, 2)
            })
    
    # Insert sources data
    for source in sources_data:
        cursor.execute(
            "INSERT INTO risk_sources (risk_metric_id, source_name, contribution_pct) VALUES (?, ?, ?)",
            (source["risk_metric_id"], source["source_name"], source["contribution_pct"])
        )
    
    # Insert capital ratios data
    for ratio in capital_ratios_data:
        cursor.execute(
            "INSERT INTO capital_ratios (ratio_type, value, reporting_date, status) VALUES (?, ?, ?, ?)",
            (ratio["ratio_type"], ratio["value"], ratio["reporting_date"], ratio["status"])
        )
    
    conn.commit()
    conn.close()
    
    # Return summary
    num_metrics = len(metrics_data)
    num_sources = len(sources_data)
    num_days = len(set(metric["reporting_date"] for metric in metrics_data))
    
    return {
        "metrics_generated": num_metrics,
        "sources_generated": num_sources,
        "days_of_data": num_days,
        "risk_types": list(risk_types.keys()),
        "db_path": db_path if db_path else DEFAULT_DB_PATH
    }

def print_summary(summary):
    """Print a summary of the generated data"""
    print("\n" + "=" * 50)
    print(" BCBS 239 Risk Data Generator - Summary ")
    print("=" * 50)
    
    print(f"\nDatabase: {summary['db_path']}")
    print(f"Generated {summary['metrics_generated']} risk metrics across {summary['days_of_data']} days")
    print(f"Generated {summary['sources_generated']} risk source contributions")
    
    print("\nRisk Types:")
    for risk_type in summary['risk_types']:
        print(f"  - {risk_type}")
    
    print("\nUse db_cli.py to explore the data. For example:")
    print(f"  python db_cli.py --db-path \"{summary['db_path']}\" view risk_metrics -r 5")
    print(f"  python db_cli.py --db-path \"{summary['db_path']}\" query \"SELECT * FROM risk_metrics WHERE reporting_date = date('now')\"")
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BCBS 239 Risk Data Generator")
    parser.add_argument("--db-path", help="Path to the SQLite database file", default=DEFAULT_DB_PATH)
    parser.add_argument("--days", type=int, help="Number of days of historical data to generate", default=90)
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt and overwrite existing data")
    args = parser.parse_args()
    
    print("BCBS 239 Risk Data Generator")
    print(f"Database path: {args.db_path}")
    
    # Check if database exists
    db_exists = os.path.exists(args.db_path)
    
    # Create tables
    create_risk_tables(args.db_path)
    
    # Ask for confirmation if database exists and tables have data
    if db_exists and not args.force:
        conn = get_db_connection(args.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('risk_metrics', 'risk_sources')")
        table_count = cursor.fetchone()[0]
        
        if table_count > 0:
            cursor.execute("SELECT COUNT(*) FROM risk_metrics")
            metric_count = cursor.fetchone()[0]
            conn.close()
            
            if metric_count > 0:
                print(f"Found existing risk data ({metric_count} records).")
                confirm = input("Do you want to replace this data? (y/n): ")
                if confirm.lower() != 'y':
                    print("Operation cancelled.")
                    exit()
    
    # Generate data
    print("\nGenerating risk data...")
    days = args.days
    if not args.force and not args.days:
        days_input = input(f"How many days of historical data to generate? (default: {days}): ")
        if days_input:
            days = int(days_input)
    
    summary = generate_random_risk_data(days, args.db_path)
    print_summary(summary) 