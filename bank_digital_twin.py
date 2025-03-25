from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class TradeExecution(Base):
    """Front Office - Initial trade execution data"""
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
    """Middle Office - Trade validation and verification"""
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
    """Middle Office - Trade enrichment with market data"""
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
    """Risk Management - Market and credit risk calculations"""
    __tablename__ = 'risk_calculation'
    
    id = Column(Integer, primary_key=True)
    enrichment_id = Column(Integer, ForeignKey('trade_enrichment.id'), nullable=False)
    market_risk_exposure = Column(Float)  # VaR
    credit_risk_exposure = Column(Float)
    calculation_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    enrichment = relationship("TradeEnrichment", back_populates="risk_calculation")
    settlement = relationship("SettlementPreparation", back_populates="risk_calculation", uselist=False)
    
    def __repr__(self):
        return f"<RiskCalculation(id={self.id}, market_risk_exposure={self.market_risk_exposure})>"


class SettlementPreparation(Base):
    """Back Office - Settlement and payment processing"""
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
    """Compliance - Regulatory reporting and compliance"""
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

# Utility functions to generate and promote trades through the lineage
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
    from datetime import datetime, timedelta
    
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
    
    return trade


def promote_trade(db_session, trade_id, target_stage="regulatory_reporting"):
    """
    Promote a trade through the lineage stages up to the specified target stage
    
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
    
    stages = ["validation", "enrichment", "risk_calculation", "settlement", "regulatory_reporting"]
    target_index = stages.index(target_stage) if target_stage in stages else len(stages) - 1
    
    # Stage 1: Validation
    if target_index >= 0:
        if not trade.validation:
            validation = TradeValidation(
                execution_id=trade.id,
                validation_status="Confirmed",
                trade_ref_number=f"{trade.counterparty[:2].upper()}-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
                settlement_date=datetime.now() + timedelta(days=3),
                validated_at=datetime.now()
            )
            db_session.add(validation)
            db_session.commit()
        else:
            validation = trade.validation
    
    # Stage 2: Enrichment
    if target_index >= 1:
        if not validation.enrichment:
            enrichment = TradeEnrichment(
                validation_id=validation.id,
                market_data_source=random.choice(["Bloomberg", "Refinitiv", "S&P Capital IQ"]),
                bond_yield=round(random.uniform(2.0, 5.0), 2) if trade.asset_class == "Bond" else None,
                sector=random.choice(["Corporate Debt", "Government", "Financial", "Technology", "Healthcare"]),
                enriched_at=datetime.now()
            )
            db_session.add(enrichment)
            db_session.commit()
        else:
            enrichment = validation.enrichment
    
    # Stage 3: Risk Calculation
    if target_index >= 2:
        if not enrichment.risk_calculation:
            notional = trade.notional_amount
            risk_calc = RiskCalculation(
                enrichment_id=enrichment.id,
                market_risk_exposure=round(notional * random.uniform(0.03, 0.08)),  # 3-8% of notional
                credit_risk_exposure=round(notional * random.uniform(0.15, 0.30)),  # 15-30% of notional
                calculation_timestamp=datetime.now()
            )
            db_session.add(risk_calc)
            db_session.commit()
        else:
            risk_calc = enrichment.risk_calculation
    
    # Stage 4: Settlement Preparation
    if target_index >= 3:
        if not risk_calc.settlement:
            settlement = SettlementPreparation(
                risk_calculation_id=risk_calc.id,
                settlement_status="Pending",
                payment_confirmation="Awaiting",
                settlement_timestamp=datetime.now()
            )
            db_session.add(settlement)
            db_session.commit()
        else:
            settlement = risk_calc.settlement
    
    # Stage 5: Regulatory Reporting
    if target_index >= 4:
        if not settlement.regulatory_reporting:
            reporting = RegulatoryReporting(
                settlement_id=settlement.id,
                regulation="BCBS 239",
                reported_to="European Banking Authority (EBA)",
                report_submission_date=datetime.now() + timedelta(days=1),
                is_submitted=False,
                reporting_timestamp=datetime.now()
            )
            db_session.add(reporting)
            db_session.commit()
    
    # Return the updated lineage
    return get_trade_lineage(db_session, trade_id)


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
