#!/usr/bin/env python3
"""
Test script for bank_digital_twin.py
Creates a sample transaction, promotes it through all stages, and generates a BCBS report summary
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tabulate import tabulate

# Import our models
from bank_digital_twin import Base, TradeExecution, TradeValidation, TradeEnrichment, \
    RiskCalculation, SettlementPreparation, RegulatoryReporting, \
    generate_sample_trade, promote_trade, get_trade_lineage

def setup_database():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def generate_bcbs_report(db_session):
    """Generate a BCBS 239 compliance report from all regulatory reporting entries"""
    # Query all trades with regulatory reporting
    query = db_session.query(
        TradeExecution.trade_id,
        TradeExecution.counterparty,
        TradeExecution.notional_amount,
        RiskCalculation.market_risk_exposure,
        RiskCalculation.credit_risk_exposure,
        SettlementPreparation.settlement_status,
        RegulatoryReporting.regulation,
        RegulatoryReporting.reported_to,
        RegulatoryReporting.is_submitted
    ).join(
        TradeValidation, TradeExecution.id == TradeValidation.execution_id
    ).join(
        TradeEnrichment, TradeValidation.id == TradeEnrichment.validation_id
    ).join(
        RiskCalculation, TradeEnrichment.id == RiskCalculation.enrichment_id
    ).join(
        SettlementPreparation, RiskCalculation.id == SettlementPreparation.risk_calculation_id
    ).join(
        RegulatoryReporting, SettlementPreparation.id == RegulatoryReporting.settlement_id
    ).all()
    
    # Format the report data
    report_data = []
    for row in query:
        trade_id, counterparty, notional, market_risk, credit_risk, settlement, regulation, reported_to, is_submitted = row
        
        report_data.append([
            trade_id,
            counterparty,
            f"${notional:,.0f}",
            f"${market_risk:,.0f}",
            f"${credit_risk:,.0f}",
            settlement,
            regulation,
            reported_to,
            "✅ Submitted" if is_submitted else "⏳ Pending"
        ])
    
    return report_data

def print_lineage_summary(lineage):
    """Print a summary of the trade lineage"""
    print("\n" + "="*80)
    print(f"🔍 TRADE LINEAGE SUMMARY FOR TRADE {lineage['trade_execution']['trade_id']}")
    print("="*80)
    
    # Print trade execution details
    exec_data = lineage['trade_execution']
    print(f"\n📋 TRADE EXECUTION - FRONT OFFICE")
    print(f"   Trade ID:       {exec_data['trade_id']}")
    print(f"   Asset Class:    {exec_data['asset_class']}")
    print(f"   Counterparty:   {exec_data['counterparty']}")
    print(f"   Notional:       ${exec_data['notional_amount']:,.2f}")
    print(f"   Execution Time: {exec_data['execution_timestamp']}")
    print(f"   Status:         {exec_data['status']}")
    
    # Print validation details if available
    if 'trade_validation' in lineage:
        val_data = lineage['trade_validation']
        print(f"\n📋 TRADE VALIDATION - MIDDLE OFFICE")
        print(f"   Status:         {val_data['validation_status']}")
        print(f"   Reference #:    {val_data['trade_ref_number']}")
        print(f"   Settlement:     {val_data['settlement_date']}")
    
    # Print enrichment details if available
    if 'trade_enrichment' in lineage:
        enr_data = lineage['trade_enrichment']
        print(f"\n📋 TRADE ENRICHMENT - MIDDLE OFFICE")
        print(f"   Data Source:    {enr_data['market_data_source']}")
        if enr_data['bond_yield']:
            print(f"   Bond Yield:     {enr_data['bond_yield']}%")
        print(f"   Sector:         {enr_data['sector']}")
    
    # Print risk calculation details if available
    if 'risk_calculation' in lineage:
        risk_data = lineage['risk_calculation']
        print(f"\n📋 RISK CALCULATION - RISK MANAGEMENT")
        print(f"   Market Risk:    ${risk_data['market_risk_exposure']:,.2f}")
        print(f"   Credit Risk:    ${risk_data['credit_risk_exposure']:,.2f}")
    
    # Print settlement details if available
    if 'settlement_preparation' in lineage:
        set_data = lineage['settlement_preparation']
        print(f"\n📋 SETTLEMENT PREPARATION - BACK OFFICE")
        print(f"   Status:         {set_data['settlement_status']}")
        print(f"   Payment:        {set_data['payment_confirmation']}")
    
    # Print regulatory reporting details if available
    if 'regulatory_reporting' in lineage:
        reg_data = lineage['regulatory_reporting']
        print(f"\n📋 REGULATORY REPORTING - COMPLIANCE")
        print(f"   Regulation:     {reg_data['regulation']}")
        print(f"   Reported To:    {reg_data['reported_to']}")
        print(f"   Submission:     {reg_data['report_submission_date']}")
        print(f"   Status:         {'Submitted' if reg_data['is_submitted'] else 'Pending'}")
        

def print_bcbs_report(report_data):
    """Print a formatted BCBS report table"""
    headers = [
        "Trade ID", "Counterparty", "Notional", "Market Risk", "Credit Risk", 
        "Settlement", "Regulation", "Reported To", "Status"
    ]
    
    print("\n" + "="*100)
    print(f"📊 BCBS 239 COMPLIANCE REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)
    
    if not report_data:
        print("\nNo reportable trades found.")
    else:
        print(tabulate(report_data, headers=headers, tablefmt="grid"))
        print(f"\nTotal Trades: {len(report_data)}")
        
        # Calculate some risk metrics
        total_notional = sum(float(row[2].replace('$', '').replace(',', '')) for row in report_data)
        total_market_risk = sum(float(row[3].replace('$', '').replace(',', '')) for row in report_data)
        total_credit_risk = sum(float(row[4].replace('$', '').replace(',', '')) for row in report_data)
        
        print(f"Total Notional Amount: ${total_notional:,.2f}")
        print(f"Total Market Risk Exposure: ${total_market_risk:,.2f} ({total_market_risk/total_notional*100:.2f}%)")
        print(f"Total Credit Risk Exposure: ${total_credit_risk:,.2f} ({total_credit_risk/total_notional*100:.2f}%)")

def generate_multiple_trades(db_session, count=10):
    """Generate multiple sample trades"""
    trades = []
    print(f"\nGenerating {count} sample trades:")
    
    for i in range(1, count + 1):
        trade_id = f"T{10000 + i}"
        trade = generate_sample_trade(db_session, trade_id)
        trades.append(trade)
        print(f"  ✓ [{i}/{count}] Created trade {trade.trade_id} with {trade.counterparty}")
    
    return trades

def process_trades_batch(db_session, trades):
    """Process all trades through the entire lifecycle"""
    total = len(trades)
    print(f"\nPromoting {total} trades through all processing stages:")
    
    lineages = []
    for i, trade in enumerate(trades, 1):
        lineage = promote_trade(db_session, trade.trade_id)
        lineages.append(lineage)
        
        # Print progress
        print(f"  ✓ [{i}/{total}] Processed {trade.trade_id} ({trade.counterparty})")
    
    return lineages

def finalize_regulatory_reporting(db_session):
    """Mark all regulatory reports as submitted"""
    reports = db_session.query(RegulatoryReporting).all()
    total = len(reports)
    
    print(f"\nFinalizing {total} regulatory reports:")
    
    for i, report in enumerate(reports, 1):
        report.is_submitted = True
        print(f"  ✓ [{i}/{total}] Marked report for settlement ID {report.settlement_id} as submitted")
    
    db_session.commit()

def main():
    """Main function to test the bank digital twin with multiple transactions"""
    print("\n🏦 BANK DIGITAL TWIN - MULTI-TRANSACTION LINEAGE DEMO")
    print("="*60)
    
    # Number of trades to generate
    num_trades = 10
    
    # Setup the database
    print("\n[1/4] Setting up in-memory database...")
    db_session = setup_database()
    
    # Generate multiple sample trades
    print("\n[2/4] Generating sample trades...")
    trades = generate_multiple_trades(db_session, num_trades)
    
    # Process all trades through the lineage
    print("\n[3/4] Processing trades through all stages...")
    lineages = process_trades_batch(db_session, trades)
    
    # Finalize all regulatory reports
    print("\n[4/4] Finalizing regulatory reporting...")
    finalize_regulatory_reporting(db_session)
    
    # Generate reports
    print("\n[5/4] Generating reports...")
    
    # Print a detailed lineage for the first trade as an example
    print("\n📋 EXAMPLE TRADE LINEAGE (First Trade)")
    print_lineage_summary(lineages[0])
    
    # Generate and print the BCBS report for all trades
    report_data = generate_bcbs_report(db_session)
    print_bcbs_report(report_data)
    
    print(f"\n✅ Demo completed successfully! Processed {num_trades} trades.\n")


if __name__ == "__main__":
    main()
