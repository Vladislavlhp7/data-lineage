import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import RiskLineageNetwork from './RiskLineageNetwork';
import './BCBS239Report.css';

function RiskDetailPage() {
    const { id: riskTypeParam } = useParams();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // Convert from API format (credit_risk) to component format (credit)
    const mappedRiskType = riskTypeParam === 'credit_risk' ? 'credit' : 
                          riskTypeParam === 'market_risk' ? 'market' : 
                          riskTypeParam;

    useEffect(() => {
        // Give time for the RiskLineageNetwork component to initialize
        const timer = setTimeout(() => {
            setLoading(false);
        }, 500);
        
        return () => clearTimeout(timer);
    }, []);

    if (loading) {
        return (
            <div className="risk-detail-page loading-container">
                <div className="loading-spinner">
                    <i className="fas fa-spinner fa-spin"></i>
                    <p>Loading Risk Lineage Data...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="risk-detail-page error-container">
                <div className="error-message">
                    <i className="fas fa-exclamation-triangle"></i>
                    <p>{error}</p>
                    <Link to="/bcbs-report" className="back-link">
                        <i className="fas fa-arrow-left"></i> Back to Report
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="risk-detail-page">
            <div className="detail-header">
                <h2>Risk Lineage: {riskTypeParam.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</h2>
                <Link to="/bcbs-report" className="back-link">
                    <i className="fas fa-arrow-left"></i> Back to Report
                </Link>
            </div>
            
            <div className="detail-content">
                <RiskLineageNetwork 
                    riskType={mappedRiskType}
                    onClose={() => {}} // No-op since we're using the back button
                />
            </div>
        </div>
    );
}

export default RiskDetailPage; 