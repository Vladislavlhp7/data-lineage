import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './BCBS239Report.css';

function BCBS239Report() {
    const [selectedRisk, setSelectedRisk] = useState(null);
    const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

    // Sample BCBS 239 report data
    const riskData = {
        creditRisk: {
            value: '8.7%',
            rwa: '€245.3M',
            trend: 'increasing',
            sources: ['Loan Portfolio', 'Corporate Bonds', 'Retail Mortgages'],
            lineageId: 'cr-001',
            description: 'Risk arising from borrower default',
            color: '#e74c3c'
        },
        marketRisk: {
            value: '3.2%',
            rwa: '€98.6M',
            trend: 'stable',
            sources: ['Trading Book', 'FX Positions', 'Derivatives'],
            lineageId: 'mr-002',
            description: 'Risk from market movements and volatility',
            color: '#3498db'
        },
        operationalRisk: {
            value: '2.1%',
            rwa: '€65.4M',
            trend: 'decreasing',
            sources: ['Process Errors', 'System Failures', 'External Events'],
            lineageId: 'or-003',
            description: 'Risk from inadequate processes, people and systems',
            color: '#f39c12'
        },
        liquidityRisk: {
            value: '12%',
            rwa: 'N/A',
            trend: 'stable',
            sources: ['Deposit Base', 'Wholesale Funding', 'Liquid Assets'],
            lineageId: 'lr-004',
            description: 'LCR (Liquidity Coverage Ratio)',
            color: '#27ae60'
        },
        concentrationRisk: {
            value: '14.3%',
            rwa: '€54.7M',
            trend: 'increasing',
            sources: ['Sector Exposure', 'Geographic Concentration', 'Single Names'],
            lineageId: 'cn-005',
            description: 'Risk from concentrated exposures',
            color: '#9b59b6'
        }
    };

    // Total capital ratio calculation (example)
    const totalCapitalRatio = '15.6%';
    const capitalAdequacyStatus = 'Compliant';

    const handleRiskHover = (riskKey, event) => {
        setSelectedRisk(riskKey);
        setTooltipPosition({
            x: event.clientX,
            y: event.clientY
        });
    };

    const handleRiskClick = (riskKey) => {
        // Here you could navigate to a detailed view or transaction lineage
        console.log(`Clicked on ${riskKey} with lineage ID: ${riskData[riskKey].lineageId}`);
        // Example: history.push(`/risk-lineage/${riskData[riskKey].lineageId}`);
    };

    const handleMouseLeave = () => {
        setSelectedRisk(null);
    };

    const getTrendIcon = (trend) => {
        switch(trend) {
            case 'increasing':
                return <i className="fas fa-arrow-up trend-up"></i>;
            case 'decreasing': 
                return <i className="fas fa-arrow-down trend-down"></i>;
            default:
                return <i className="fas fa-arrows-alt-h trend-stable"></i>;
        }
    };

    return (
        <div className="bcbs-report-container">
            <h1>BCBS 239 Regulatory Report</h1>
            <div className="report-date">Reporting Date: {new Date().toLocaleDateString()}</div>
            
            <div className="report-summary">
                <div className="summary-box">
                    <h3>Total Capital Ratio</h3>
                    <div className="ratio-value">{totalCapitalRatio}</div>
                    <div className="status-indicator compliant">{capitalAdequacyStatus}</div>
                </div>
                
                <div className="summary-box">
                    <h3>Risk Profile</h3>
                    <div className="risk-chart">
                        {Object.entries(riskData).map(([key, data]) => (
                            <div 
                                key={key}
                                className="risk-bar"
                                style={{ 
                                    height: `${parseFloat(data.value) * 5}px`,
                                    backgroundColor: data.color
                                }}
                                title={`${key}: ${data.value}`}
                            />
                        ))}
                    </div>
                </div>
            </div>
            
            <div className="risk-metrics-table">
                <h2>Risk Metrics</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Risk Type</th>
                            <th>Value</th>
                            <th>Risk-Weighted Assets</th>
                            <th>Trend</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {Object.entries(riskData).map(([key, data]) => (
                            <tr key={key}>
                                <td>{key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}</td>
                                <td
                                    className="risk-value hover-effect"
                                    onMouseEnter={(e) => handleRiskHover(key, e)}
                                    onMouseLeave={handleMouseLeave}
                                    onClick={() => handleRiskClick(key)}
                                >
                                    {data.value}
                                </td>
                                <td>{data.rwa}</td>
                                <td className="trend-cell">
                                    {getTrendIcon(data.trend)}
                                    {data.trend}
                                </td>
                                <td>
                                    <Link to={`/risk-detail/${data.lineageId}`} className="view-details-btn">
                                        <i className="fas fa-chart-line"></i> View Lineage
                                    </Link>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            
            {selectedRisk && (
                <div 
                    className="risk-tooltip" 
                    style={{ 
                        top: `${tooltipPosition.y + 10}px`, 
                        left: `${tooltipPosition.x + 10}px` 
                    }}
                >
                    <h4>{selectedRisk.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}</h4>
                    <p>{riskData[selectedRisk].description}</p>
                    <div className="tooltip-sources">
                        <strong>Data Sources:</strong>
                        <ul>
                            {riskData[selectedRisk].sources.map((source, index) => (
                                <li key={index}>{source}</li>
                            ))}
                        </ul>
                    </div>
                </div>
            )}
            
            <div className="report-footer">
                <div className="disclaimer">
                    <h3>Disclaimer</h3>
                    <p>This report is generated in compliance with Basel Committee on Banking Supervision (BCBS) Regulation 239. 
                    It provides an overview of the bank's risk data aggregation capabilities and risk reporting practices.</p>
                </div>
                <div className="report-actions">
                    <button className="report-btn">
                        <i className="fas fa-download"></i> Export PDF
                    </button>
                    <button className="report-btn">
                        <i className="fas fa-history"></i> View History
                    </button>
                </div>
            </div>
        </div>
    );
}

export default BCBS239Report; 