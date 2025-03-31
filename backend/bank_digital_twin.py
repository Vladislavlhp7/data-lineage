from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Date, Text, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime, date, timedelta
import random
import numpy as np

# Database setup
DATABASE_URL = "sqlite:///./bank_digital_twin.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# BCBS 239 Risk Models
class RiskMetric(Base):
    __tablename__ = 'risk_metrics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    risk_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    rwa = Column(Float)  # Risk-weighted assets
    trend = Column(String(20))  # increasing, decreasing, stable
    reporting_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sources = relationship("RiskSource", back_populates="risk_metric", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RiskMetric(id={self.id}, risk_type='{self.risk_type}', value={self.value})>"

class RiskSource(Base):
    __tablename__ = 'risk_sources'
    id = Column(Integer, primary_key=True, autoincrement=True)
    risk_metric_id = Column(Integer, ForeignKey('risk_metrics.id'), nullable=False)
    source_name = Column(String(100), nullable=False)
    contribution_pct = Column(Float, nullable=False)  # Percentage contribution
    
    # Relationships
    risk_metric = relationship("RiskMetric", back_populates="sources")
    
    def __repr__(self):
        return f"<RiskSource(id={self.id}, source='{self.source_name}', contribution={self.contribution_pct}%)>"

class RiskThreshold(Base):
    __tablename__ = 'risk_thresholds'
    id = Column(Integer, primary_key=True, autoincrement=True)
    risk_type = Column(String(50), nullable=False)
    warning_threshold = Column(Float, nullable=False)
    critical_threshold = Column(Float, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<RiskThreshold(id={self.id}, risk_type='{self.risk_type}')>"

class CapitalRatio(Base):
    __tablename__ = 'capital_ratios'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ratio_type = Column(String(50), nullable=False)  # total_capital_ratio, tier1_capital_ratio, etc.
    value = Column(Float, nullable=False)
    reporting_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)  # Compliant, Warning, Non-Compliant
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CapitalRatio(id={self.id}, type='{self.ratio_type}', value={self.value})>"

# Original models
class TradeExecution(Base):
    __tablename__ = 'trade_execution'
    id = Column(Integer, primary_key=True)
    trade_id = Column(String(50), unique=True, nullable=False)
    asset_class = Column(String(50), nullable=False)
    counterparty = Column(String(100), nullable=False)
    notional_amount = Column(Float, nullable=False)
    execution_timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="Executed")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    validation = relationship("TradeValidation", back_populates="execution", uselist=False)

    def __repr__(self):
        return f"<TradeExecution(trade_id='{self.trade_id}', counterparty='{self.counterparty}')>"

class TradeValidation(Base):
    __tablename__ = 'trade_validation'
    id = Column(Integer, primary_key=True)
    execution_id = Column(Integer, ForeignKey('trade_execution.id'), nullable=False)
    validation_status = Column(String(50), default="Pending")
    trade_ref_number = Column(String(100))
    settlement_date = Column(DateTime)
    validated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    execution = relationship("TradeExecution", back_populates="validation")
    enrichment = relationship("TradeEnrichment", back_populates="validation", uselist=False)

    def __repr__(self):
        return f"<TradeValidation(id={self.id}, validation_status='{self.validation_status}')>"

class TradeEnrichment(Base):
    __tablename__ = 'trade_enrichment'
    id = Column(Integer, primary_key=True)
    validation_id = Column(Integer, ForeignKey('trade_validation.id'), nullable=False)
    market_data_source = Column(String(100))
    bond_yield = Column(Float)
    sector = Column(String(100))
    enriched_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    validation = relationship("TradeValidation", back_populates="enrichment")
    risk_calculation = relationship("RiskCalculation", back_populates="enrichment", uselist=False)

    def __repr__(self):
        return f"<TradeEnrichment(id={self.id}, market_data_source='{self.market_data_source}')>"

class RiskCalculation(Base):
    __tablename__ = 'risk_calculation'
    id = Column(Integer, primary_key=True)
    enrichment_id = Column(Integer, ForeignKey('trade_enrichment.id'), nullable=False)
    market_risk_exposure = Column(Float)
    credit_risk_exposure = Column(Float)
    calculation_timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    enrichment = relationship("TradeEnrichment", back_populates="risk_calculation")
    settlement = relationship("SettlementPreparation", back_populates="risk_calculation", uselist=False)

    def __repr__(self):
        return f"<RiskCalculation(id={self.id}, market_risk_exposure={self.market_risk_exposure})>"

class SettlementPreparation(Base):
    __tablename__ = 'settlement_preparation'
    id = Column(Integer, primary_key=True)
    risk_calculation_id = Column(Integer, ForeignKey('risk_calculation.id'), nullable=False)
    settlement_status = Column(String(50), default="Pending")
    payment_confirmation = Column(String(50), default="Awaiting")
    settlement_timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    risk_calculation = relationship("RiskCalculation", back_populates="settlement")
    regulatory_reporting = relationship("RegulatoryReporting", back_populates="settlement", uselist=False)

    def __repr__(self):
        return f"<SettlementPreparation(id={self.id}, settlement_status='{self.settlement_status}')>"

class RegulatoryReporting(Base):
    __tablename__ = 'regulatory_reporting'
    id = Column(Integer, primary_key=True)
    settlement_id = Column(Integer, ForeignKey('settlement_preparation.id'), nullable=False)
    regulation = Column(String(100))
    reported_to = Column(String(200))
    report_submission_date = Column(DateTime)
    is_submitted = Column(Boolean, default=False)
    reporting_timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    settlement = relationship("SettlementPreparation", back_populates="regulatory_reporting")

    def __repr__(self):
        return f"<RegulatoryReporting(id={self.id}, regulation='{self.regulation}', is_submitted={self.is_submitted})>"

# Initialize the risk data
def initialize_risk_data(db_session):
    """
    Initialize risk data for BCBS 239 testing if it doesn't exist
    """
    # Check if data already exists
    risk_count = db_session.query(RiskMetric).count()
    if risk_count > 0:
        return  # Data already exists
    
    # Risk types and thresholds
    risk_types = {
        "credit_risk": {
            "value": 8.7,
            "rwa": 245.3,
            "trend": "increasing",
            "sources": [
                ("Loan Portfolio", 45.0),
                ("Corporate Bonds", 30.0),
                ("Retail Mortgages", 25.0)
            ],
            "warning": 10.0,
            "critical": 12.0
        },
        "market_risk": {
            "value": 3.2,
            "rwa": 98.6,
            "trend": "stable",
            "sources": [
                ("Trading Book", 50.0),
                ("FX Positions", 30.0),
                ("Derivatives", 20.0)
            ],
            "warning": 4.5,
            "critical": 6.0
        },
        "operational_risk": {
            "value": 2.1,
            "rwa": 65.4,
            "trend": "decreasing",
            "sources": [
                ("Process Errors", 40.0),
                ("System Failures", 35.0),
                ("External Events", 25.0)
            ],
            "warning": 3.0,
            "critical": 4.0
        },
        "liquidity_risk": {
            "value": 112.0,
            "rwa": None,
            "trend": "stable",
            "sources": [
                ("Deposit Base", 50.0),
                ("Wholesale Funding", 30.0),
                ("Liquid Assets", 20.0)
            ],
            "warning": 105.0,  # LCR should be above 100%
            "critical": 100.0
        },
        "concentration_risk": {
            "value": 14.3,
            "rwa": 54.7,
            "trend": "increasing",
            "sources": [
                ("Sector Exposure", 40.0),
                ("Geographic Concentration", 35.0),
                ("Single Names", 25.0)
            ],
            "warning": 16.0,
            "critical": 20.0
        }
    }
    
    # Today's date for reporting
    today = date.today()
    
    # Add risk metrics
    for risk_type, data in risk_types.items():
        # Create risk metric
        risk_metric = RiskMetric(
            risk_type=risk_type,
            value=data["value"],
            rwa=data["rwa"],
            trend=data["trend"],
            reporting_date=today
        )
        db_session.add(risk_metric)
        db_session.flush()  # Flush to get the ID
        
        # Add sources
        for source_name, contribution in data["sources"]:
            source = RiskSource(
                risk_metric_id=risk_metric.id,
                source_name=source_name,
                contribution_pct=contribution
            )
            db_session.add(source)
        
        # Add threshold
        threshold = RiskThreshold(
            risk_type=risk_type,
            warning_threshold=data["warning"],
            critical_threshold=data["critical"]
        )
        db_session.add(threshold)
    
    # Add capital ratios
    capital_ratios = [
        {
            "ratio_type": "total_capital_ratio",
            "value": 15.6,
            "status": "Compliant"
        },
        {
            "ratio_type": "tier1_capital_ratio",
            "value": 13.2,
            "status": "Compliant"
        }
    ]
    
    for ratio_data in capital_ratios:
        ratio = CapitalRatio(
            ratio_type=ratio_data["ratio_type"],
            value=ratio_data["value"],
            reporting_date=today,
            status=ratio_data["status"]
        )
        db_session.add(ratio)
    
    db_session.commit()

# Ensure tables are created
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        # Initialize risk data
        initialize_risk_data(db)
        yield db
    finally:
        db.close()

# Utility functions to query the full lineage of a trade
def get_trade_lineage(db_session, trade_id):
    """
    Retrieve the complete lineage of a trade from execution to regulatory reporting
    
    Args:
        db_session: SQLAlchemy session
        trade_id: Unique trade identifier
        
    Returns:
        dict: Complete lineage of the trade with all transformation steps
    """
    trade = db_session.query(TradeExecution).filter_by(trade_id=trade_id).first()
    if not trade:
        return {"error": "Trade not found"}
    
    # Build complete lineage
    lineage = {
        "trade_execution": {
            "trade_id": trade.trade_id,
            "asset_class": trade.asset_class,
            "counterparty": trade.counterparty,
            "notional_amount": trade.notional_amount,
            "execution_timestamp": trade.execution_timestamp,
            "status": trade.status
        }
    }
    
    if trade.validation:
        validation = trade.validation
        lineage["trade_validation"] = {
            "validation_status": validation.validation_status,
            "trade_ref_number": validation.trade_ref_number,
            "settlement_date": validation.settlement_date
        }
        
        if validation.enrichment:
            enrichment = validation.enrichment
            lineage["trade_enrichment"] = {
                "market_data_source": enrichment.market_data_source,
                "bond_yield": enrichment.bond_yield,
                "sector": enrichment.sector
            }
            
            if enrichment.risk_calculation:
                risk = enrichment.risk_calculation
                lineage["risk_calculation"] = {
                    "market_risk_exposure": risk.market_risk_exposure,
                    "credit_risk_exposure": risk.credit_risk_exposure
                }
                
                if risk.settlement:
                    settlement = risk.settlement
                    lineage["settlement_preparation"] = {
                        "settlement_status": settlement.settlement_status,
                        "payment_confirmation": settlement.payment_confirmation
                    }
                    
                    if settlement.regulatory_reporting:
                        reporting = settlement.regulatory_reporting
                        lineage["regulatory_reporting"] = {
                            "regulation": reporting.regulation,
                            "reported_to": reporting.reported_to,
                            "report_submission_date": reporting.report_submission_date,
                            "is_submitted": reporting.is_submitted
                        }
    
    return lineage

def update_risk_metrics_from_transaction(db_session, trade, stage="execution"):
    """
    Update risk metrics based on a new transaction or transaction promotion
    
    Args:
        db_session: SQLAlchemy session
        trade: TradeExecution object
        stage: Current stage of the trade ("execution", "validation", "risk_calculation", etc.)
        
    Returns:
        dict: Summary of updates made to risk metrics
    """
    # Get today's date for reporting
    today = date.today()
    
    # Check if we have risk metrics for today
    latest_metrics = db_session.query(RiskMetric).filter(
        func.date(RiskMetric.reporting_date) == today
    ).all()
    
    # If no metrics exist for today, copy the latest ones and modify them
    if not latest_metrics:
        # Find the latest date with metrics
        latest_date_result = db_session.execute(
            text("SELECT MAX(reporting_date) FROM risk_metrics")
        ).fetchone()
        
        if not latest_date_result or not latest_date_result[0]:
            # No previous metrics exist, can't update
            return {"status": "No existing metrics to update"}
        
        latest_date = latest_date_result[0]
        
        # Copy the latest metrics to today
        copy_query = text("""
        INSERT INTO risk_metrics (risk_type, value, rwa, trend, reporting_date)
        SELECT risk_type, value, rwa, trend, :today
        FROM risk_metrics
        WHERE reporting_date = :latest_date
        """)
        
        db_session.execute(copy_query, {"today": today, "latest_date": latest_date})
        db_session.commit()
        
        # Now get the newly created metrics for today
        latest_metrics = db_session.query(RiskMetric).filter(
            func.date(RiskMetric.reporting_date) == today
        ).all()
        
        # Also copy risk sources
        for metric in latest_metrics:
            # Find the corresponding old metric
            old_metric = db_session.query(RiskMetric).filter(
                RiskMetric.risk_type == metric.risk_type,
                RiskMetric.reporting_date == latest_date
            ).first()
            
            if old_metric:
                # Get all sources from the old metric
                old_sources = db_session.query(RiskSource).filter(
                    RiskSource.risk_metric_id == old_metric.id
                ).all()
                
                # Create new sources based on old ones
                for source in old_sources:
                    new_source = RiskSource(
                        risk_metric_id=metric.id,
                        source_name=source.source_name,
                        contribution_pct=source.contribution_pct
                    )
                    db_session.add(new_source)
        
        db_session.commit()
    
    # Define impact factors based on transaction properties
    impact_factors = {
        "asset_class": {
            "Bond": {"credit_risk": 0.05, "market_risk": 0.02, "liquidity_risk": 0.01},
            "Equity": {"credit_risk": 0.01, "market_risk": 0.07, "liquidity_risk": 0.02},
            "Derivative": {"credit_risk": 0.03, "market_risk": 0.08, "operational_risk": 0.04},
            "FX": {"market_risk": 0.05, "liquidity_risk": 0.03},
            "Commodity": {"market_risk": 0.06, "concentration_risk": 0.03}
        },
        "notional_scale": {  # Multipliers based on notional amount scale
            "small": 0.5,    # < 2M
            "medium": 1.0,   # 2-5M
            "large": 2.0     # > 5M
        },
        "stage": {  # Multipliers based on trade lifecycle stage
            "execution": 0.3,
            "validation": 0.5,
            "enrichment": 0.7,
            "risk_calculation": 1.0,
            "settlement": 0.8,
            "regulatory_reporting": 0.6
        }
    }
    
    # Determine notional scale
    notional = trade.notional_amount
    if notional < 2000000:
        notional_scale = "small"
    elif notional < 5000000:
        notional_scale = "medium"
    else:
        notional_scale = "large"
    
    # Calculate impact multiplier
    base_multiplier = impact_factors["notional_scale"][notional_scale] * impact_factors["stage"][stage]
    
    # Determine which risk types are affected
    asset_class = trade.asset_class
    affected_risk_types = impact_factors["asset_class"].get(asset_class, {})
    
    # Keep track of all updates made
    updates = []
    
    # Update each affected risk metric
    for risk_type, impact_factor in affected_risk_types.items():
        metric = db_session.query(RiskMetric).filter(
            RiskMetric.risk_type == risk_type,
            func.date(RiskMetric.reporting_date) == today
        ).first()
        
        if metric:
            # Calculate the actual impact (positive means risk increases)
            impact = impact_factor * base_multiplier
            
            # Scale the impact based on the notional
            scaled_impact = impact * (notional / 5000000)  # Normalize to 5M as baseline
            
            # Add some randomness for realism (-20% to +20%)
            random_factor = 1.0 + (random.random() * 0.4 - 0.2)
            final_impact = scaled_impact * random_factor
            
            # Apply the impact - store the old value for reporting
            old_value = metric.value
            
            # For liquidity risk, higher values are better (opposite impact)
            if risk_type == "liquidity_risk":
                metric.value = max(70, metric.value - final_impact)
            else:
                metric.value = max(0.5, metric.value + final_impact)
            
            # Update RWA proportionally if applicable
            if metric.rwa is not None:
                rwa_change_pct = (metric.value - old_value) / old_value
                metric.rwa = metric.rwa * (1 + rwa_change_pct)
            
            # Update the trend
            if metric.value > old_value * 1.02:  # More than 2% increase
                metric.trend = "increasing"
            elif metric.value < old_value * 0.98:  # More than 2% decrease
                metric.trend = "decreasing"
            else:
                metric.trend = "stable"
            
            updates.append({
                "risk_type": risk_type,
                "old_value": round(old_value, 2),
                "new_value": round(metric.value, 2),
                "change": round(metric.value - old_value, 2),
                "trend": metric.trend
            })
    
    # Commit all changes
    db_session.commit()
    
    return {
        "status": "success",
        "updates": updates,
        "transaction": {
            "trade_id": trade.trade_id,
            "asset_class": trade.asset_class,
            "notional": trade.notional_amount,
            "stage": stage
        }
    }

# Update the generate_sample_trade function to update risk metrics
def generate_sample_trade(db_session, trade_id=None):
    """
    Generate a sample trade execution entry in the database
    
    Args:
        db_session: SQLAlchemy session
        trade_id: Optional specific trade ID (generated if not provided)
        
    Returns:
        TradeExecution: The created trade execution object
    """
    import random
    from datetime import datetime
    
    # Sample data for random generation
    asset_classes = ["Bond", "Equity", "Derivative", "FX", "Commodity"]
    counterparties = ["Goldman Sachs", "JP Morgan", "Deutsche Bank", "BNP Paribas", "Morgan Stanley", "Credit Suisse"]
    
    # Generate trade ID if not provided
    if not trade_id:
        trade_id = f"T{random.randint(10000, 99999)}"
    
    # Create trade execution record
    trade = TradeExecution(
        trade_id=trade_id,
        asset_class=random.choice(asset_classes),
        counterparty=random.choice(counterparties),
        notional_amount=random.randint(1000000, 10000000),
        execution_timestamp=datetime.utcnow(),
        status="Executed"
    )
    
    db_session.add(trade)
    db_session.commit()
    
    # Update risk metrics based on the new trade
    update_risk_metrics_from_transaction(db_session, trade, "execution")
    
    return trade

# Update the promote_trade function to update risk metrics at each promotion
def promote_trade(db_session, trade_id, target_stage=None):
    """
    Promote a trade through the lineage stages. If `target_stage` is not provided,
    promote the trade to the next stage from its current state.
    
    Args:
        db_session: SQLAlchemy session
        trade_id: Unique trade identifier
        target_stage: The stage to promote to ('validation', 'enrichment', 
                      'risk_calculation', 'settlement', 'regulatory_reporting')
        
    Returns:
        dict: Updated lineage of the trade with all applied transformations
    """
    import random
    from datetime import datetime, timedelta

    # Find the trade
    trade = db_session.query(TradeExecution).filter_by(trade_id=trade_id).first()
    if not trade:
        return {"error": "Trade not found"}

    # Define the stages and determine the current stage
    stages = ["validation", "enrichment", "risk_calculation", "settlement", "regulatory_reporting"]
    current_stage_index = 0

    if trade.validation:
        current_stage_index = 1
    if trade.validation and trade.validation.enrichment:
        current_stage_index = 2
    if trade.validation and trade.validation.enrichment and trade.validation.enrichment.risk_calculation:
        current_stage_index = 3
    if trade.validation and trade.validation.enrichment and trade.validation.enrichment.risk_calculation and trade.validation.enrichment.risk_calculation.settlement:
        current_stage_index = 4

    # Determine the target stage index
    if target_stage:
        if target_stage not in stages:
            return {"error": f"Invalid target stage: {target_stage}"}
        target_index = stages.index(target_stage)
    else:
        # Promote to the next stage if no target_stage is provided
        target_index = current_stage_index + 1

    if target_index <= current_stage_index:
        return {"error": "Cannot promote to a previous or the same stage"}

    # Store original stage for later risk update
    original_stage = stages[current_stage_index] if current_stage_index < len(stages) else "execution"
    target_stage_name = stages[target_index] if target_index < len(stages) else "regulatory_reporting"

    # Stage 1: Validation
    if target_index >= 1 and not trade.validation:
        validation = TradeValidation(
            execution_id=trade.id,
            validation_status="Confirmed",
            trade_ref_number=f"{trade.counterparty[:2].upper()}-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            settlement_date=datetime.now() + timedelta(days=3),
            validated_at=datetime.now()
        )
        db_session.add(validation)
        db_session.commit()
        trade.validation = validation

    # Stage 2: Enrichment
    if target_index >= 2 and trade.validation and not trade.validation.enrichment:
        enrichment = TradeEnrichment(
            validation_id=trade.validation.id,
            market_data_source=random.choice(["Bloomberg", "Refinitiv", "S&P Capital IQ"]),
            bond_yield=round(random.uniform(2.0, 5.0), 2) if trade.asset_class == "Bond" else None,
            sector=random.choice(["Corporate Debt", "Government", "Financial", "Technology", "Healthcare"]),
            enriched_at=datetime.now()
        )
        db_session.add(enrichment)
        db_session.commit()
        trade.validation.enrichment = enrichment

    # Stage 3: Risk Calculation
    if target_index >= 3 and trade.validation.enrichment and not trade.validation.enrichment.risk_calculation:
        notional = trade.notional_amount
        risk_calc = RiskCalculation(
            enrichment_id=trade.validation.enrichment.id,
            market_risk_exposure=round(notional * random.uniform(0.03, 0.08)),  # 3-8% of notional
            credit_risk_exposure=round(notional * random.uniform(0.15, 0.30)),  # 15-30% of notional
            calculation_timestamp=datetime.now()
        )
        db_session.add(risk_calc)
        db_session.commit()
        trade.validation.enrichment.risk_calculation = risk_calc

    # Stage 4: Settlement Preparation
    if target_index >= 4 and trade.validation.enrichment.risk_calculation and not trade.validation.enrichment.risk_calculation.settlement:
        settlement = SettlementPreparation(
            risk_calculation_id=trade.validation.enrichment.risk_calculation.id,
            settlement_status="Pending",
            payment_confirmation="Awaiting",
            settlement_timestamp=datetime.now()
        )
        db_session.add(settlement)
        db_session.commit()
        trade.validation.enrichment.risk_calculation.settlement = settlement

    # Stage 5: Regulatory Reporting
    if target_index >= 5 and trade.validation.enrichment.risk_calculation.settlement and not trade.validation.enrichment.risk_calculation.settlement.regulatory_reporting:
        reporting = RegulatoryReporting(
            settlement_id=trade.validation.enrichment.risk_calculation.settlement.id,
            regulation="BCBS 239",
            reported_to="European Banking Authority (EBA)",
            report_submission_date=datetime.now() + timedelta(days=1),
            is_submitted=False,
            reporting_timestamp=datetime.now()
        )
        db_session.add(reporting)
        db_session.commit()
        trade.validation.enrichment.risk_calculation.settlement.regulatory_reporting = reporting

    # Update risk metrics based on the trade promotion
    risk_update = update_risk_metrics_from_transaction(db_session, trade, target_stage_name)
    
    # Return the updated lineage
    lineage = get_trade_lineage(db_session, trade_id)
    lineage["risk_impacts"] = risk_update
    
    return lineage

def create_demo_workflow(db_session):
    """
    Create a complete demo workflow with a trade passing through all stages
    
    Args:
        db_session: SQLAlchemy session
        
    Returns:
        dict: Complete lineage of the created trade
    """
    # Generate a sample trade
    trade = generate_sample_trade(db_session)
    
    # Promote it through all stages
    result = promote_trade(db_session, trade.trade_id)
    
    return result
