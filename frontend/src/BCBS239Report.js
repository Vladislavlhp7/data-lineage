import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Line, Pie } from 'react-chartjs-2';
import { 
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import './BCBS239Report.css';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

function BCBS239Report() {
    const [selectedRisk, setSelectedRisk] = useState(null);
    const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [reportData, setReportData] = useState({
        credit_risk_avg: 0,
        market_risk_avg: 0,
        latest_metrics: [],
        capital_ratios: [],
        reporting_date: ''
    });
    const [sourceData, setSourceData] = useState({});
    const [summary, setSummary] = useState(null);
    const [selectedRiskType, setSelectedRiskType] = useState('credit_risk');
    const [riskTrends, setRiskTrends] = useState(null);
    const [riskSources, setRiskSources] = useState(null);
    const [lastUpdated, setLastUpdated] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch summary data
                const response = await axios.get('http://localhost:8000/bcbs/summary');
                setReportData(response.data);
                setSummary(response.data);
                setLastUpdated(new Date());
                
                // Fetch initial risk type data
                await fetchRiskTrends(selectedRiskType);
                await fetchRiskSources(selectedRiskType);
                
                setLoading(false);
            } catch (err) {
                console.error('Error fetching BCBS data:', err);
                setError('Failed to load BCBS 239 report data');
                setLoading(false);
            }
        };

        fetchData();
        
        // Set up periodic refresh every 5 seconds to capture changes from transactions
        const refreshInterval = setInterval(() => {
            const refreshData = async () => {
                try {
                    // Fetch summary data
                    const response = await axios.get('http://localhost:8000/bcbs/summary');
                    setReportData(response.data);
                    setSummary(response.data);
                    setLastUpdated(new Date());
                    
                    // Refresh current risk type data
                    await fetchRiskTrends(selectedRiskType);
                    await fetchRiskSources(selectedRiskType);
                } catch (err) {
                    console.error('Error refreshing BCBS data:', err);
                }
            };
            refreshData();
        }, 5000);
        
        // Cleanup interval on component unmount
        return () => clearInterval(refreshInterval);
    }, []);
    
    // When selected risk type changes, fetch that data
    useEffect(() => {
        if (!loading && selectedRiskType) {
            fetchRiskTrends(selectedRiskType);
            fetchRiskSources(selectedRiskType);
        }
    }, [selectedRiskType, loading]);

    const fetchBCBSData = async () => {
        setLoading(true);
        try {
            console.log('Fetching BCBS data from the integrated database...');
            const response = await axios.get('http://localhost:8000/bcbs/summary');
            console.log('BCBS data received:', response.data);
            setReportData(response.data);
            setSummary(response.data);
            setLastUpdated(new Date());
            setLoading(false);
        } catch (err) {
            console.error("Error fetching BCBS data:", err);
            setError("Failed to fetch BCBS report data. Please try again later.");
            setLoading(false);
            
            // Fallback to sample data if API fails
            setReportData({
                credit_risk_avg: 8.7,
                market_risk_avg: 3.2,
                latest_metrics: getSampleRiskData(),
                capital_ratios: [
                    {
                        ratio_type: "total_capital_ratio",
                        value: 15.6,
                        status: "Compliant",
                        reporting_date: new Date().toISOString().split('T')[0]
                    },
                    {
                        ratio_type: "tier1_capital_ratio",
                        value: 13.2,
                        status: "Compliant",
                        reporting_date: new Date().toISOString().split('T')[0]
                    }
                ],
                reporting_date: new Date().toISOString().split('T')[0]
            });
        }
    };

    // Sample risk data as fallback
    const getSampleRiskData = () => {
        return [
            {
                risk_type: "credit_risk",
                value: 8.7,
                rwa: 245.3,
                trend: "increasing",
                reporting_date: new Date().toISOString().split('T')[0]
            },
            {
                risk_type: "market_risk",
                value: 3.2,
                rwa: 98.6,
                trend: "stable",
                reporting_date: new Date().toISOString().split('T')[0]
            },
            {
                risk_type: "operational_risk",
                value: 2.1,
                rwa: 65.4,
                trend: "decreasing",
                reporting_date: new Date().toISOString().split('T')[0]
            },
            {
                risk_type: "liquidity_risk",
                value: 112,
                rwa: null,
                trend: "stable",
                reporting_date: new Date().toISOString().split('T')[0]
            },
            {
                risk_type: "concentration_risk",
                value: 14.3,
                rwa: 54.7,
                trend: "increasing",
                reporting_date: new Date().toISOString().split('T')[0]
            }
        ];
    };

    const formatRiskType = (riskType) => {
        return riskType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    const handleRiskHover = (riskType, event) => {
        setSelectedRisk(riskType);
        setTooltipPosition({
            x: event.clientX,
            y: event.clientY
        });
    };

    const handleRiskClick = async (riskType) => {
        try {
            // If we already fetched this data, don't fetch it again
            if (sourceData[riskType]) {
                console.log(`Using cached ${riskType} sources data`);
                return;
            }

            // Fetch risk sources when a risk is clicked
            console.log(`Fetching sources for ${riskType}...`);
            const response = await axios.get(`http://localhost:8000/bcbs/risk-sources/${riskType}`);
            console.log(`${riskType} sources:`, response.data);
            
            // Store the sources data
            setSourceData(prev => ({
                ...prev,
                [riskType]: response.data.sources
            }));
        } catch (error) {
            console.error(`Error fetching ${riskType} sources:`, error);
        }
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

    // Map risk types to descriptions and colors
    const riskInfo = {
        credit_risk: {
            description: 'Risk arising from borrower default',
            color: '#e74c3c',
            sources: ['Loan Portfolio', 'Corporate Bonds', 'Retail Mortgages']
        },
        market_risk: {
            description: 'Risk from market movements and volatility',
            color: '#3498db',
            sources: ['Trading Book', 'FX Positions', 'Derivatives']
        },
        operational_risk: {
            description: 'Risk from inadequate processes, people and systems',
            color: '#f39c12',
            sources: ['Process Errors', 'System Failures', 'External Events']
        },
        liquidity_risk: {
            description: 'LCR (Liquidity Coverage Ratio)',
            color: '#27ae60',
            sources: ['Deposit Base', 'Wholesale Funding', 'Liquid Assets']
        },
        concentration_risk: {
            description: 'Risk from concentrated exposures',
            color: '#9b59b6',
            sources: ['Sector Exposure', 'Geographic Concentration', 'Single Names']
        }
    };

    // Get Total Capital Ratio
    const getTotalCapitalRatio = () => {
        const totalCapital = reportData.capital_ratios.find(ratio => ratio.ratio_type === 'total_capital_ratio');
        return totalCapital ? totalCapital.value + '%' : 'N/A';
    };

    // Get Capital Adequacy Status
    const getCapitalStatus = () => {
        const totalCapital = reportData.capital_ratios.find(ratio => ratio.ratio_type === 'total_capital_ratio');
        return totalCapital ? totalCapital.status : 'Unknown';
    };

    // Fetch risk trends for selected risk type
    const fetchRiskTrends = async (riskType) => {
        try {
            const response = await axios.get(`http://localhost:8000/bcbs/risk-trends/${riskType}`);
            setRiskTrends(response.data);
        } catch (error) {
            console.error(`Error fetching risk trends for ${riskType}:`, error);
            setError(`Failed to load risk trend data for ${riskType}`);
        }
    };

    // Fetch risk sources for selected risk type
    const fetchRiskSources = async (riskType) => {
        try {
            const response = await axios.get(`http://localhost:8000/bcbs/risk-sources/${riskType}`);
            setRiskSources(response.data);
        } catch (error) {
            console.error(`Error fetching risk sources for ${riskType}:`, error);
            setError(`Failed to load risk source data for ${riskType}`);
        }
    };

    // Handle risk type selection
    const handleRiskTypeChange = (riskType) => {
        setSelectedRiskType(riskType);
    };

    // Format chart data for risk trends
    const getTrendChartData = () => {
        if (!riskTrends || !riskTrends.trends) return null;

        // Sort trends by date
        const sortedTrends = [...riskTrends.trends].sort((a, b) => 
            new Date(a.reporting_date) - new Date(b.reporting_date));

        return {
            labels: sortedTrends.map(trend => {
                const date = new Date(trend.reporting_date);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }),
            datasets: [
                {
                    label: `${riskTrends.risk_type.replace('_', ' ')} Value`,
                    data: sortedTrends.map(trend => trend.value),
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    tension: 0.4,
                },
                {
                    label: 'RWA',
                    data: sortedTrends.map(trend => trend.rwa),
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    tension: 0.4,
                    hidden: selectedRiskType === 'liquidity_risk',
                }
            ],
        };
    };

    // Format chart data for risk sources
    const getSourcesChartData = () => {
        if (!riskSources || !riskSources.sources || riskSources.sources.length === 0) return null;

        const colors = [
            'rgba(255, 99, 132, 0.7)',
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(153, 102, 255, 0.7)',
            'rgba(255, 159, 64, 0.7)'
        ];

        return {
            labels: riskSources.sources.map(source => source.source),
            datasets: [
                {
                    data: riskSources.sources.map(source => source.contribution),
                    backgroundColor: colors.slice(0, riskSources.sources.length),
                    borderWidth: 1,
                },
            ],
        };
    };

    // Chart options
    const trendChartOptions = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            label += context.parsed.y.toFixed(2);
                        }
                        return label;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: false,
            }
        }
    };

    // Pie chart options
    const sourcesChartOptions = {
        responsive: true,
        plugins: {
            legend: {
                position: 'right',
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const label = context.label || '';
                        const value = context.parsed || 0;
                        return `${label}: ${value}%`;
                    }
                }
            }
        }
    };

    // Format date for display
    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric'
        });
    };

    // Get status color class
    const getStatusColorClass = (status) => {
        switch (status?.toLowerCase()) {
            case 'compliant':
                return 'status-compliant';
            case 'warning':
                return 'status-warning';
            case 'non-compliant':
                return 'status-non-compliant';
            default:
                return '';
        }
    };

    // Determine risk level class
    const getRiskLevelClass = (riskType, value) => {
        if (!summary) return '';

        // Define thresholds for each risk type
        const thresholds = {
            credit_risk: { warning: 10, critical: 12 },
            market_risk: { warning: 4.5, critical: 6 },
            operational_risk: { warning: 3, critical: 4 },
            liquidity_risk: { warning: 105, critical: 100 }, // For liquidity risk, lower is worse
            concentration_risk: { warning: 16, critical: 20 },
        };

        const threshold = thresholds[riskType];
        if (!threshold) return '';

        if (riskType === 'liquidity_risk') {
            // For liquidity risk, higher is better
            if (value < threshold.critical) return 'risk-critical';
            if (value < threshold.warning) return 'risk-warning';
            return 'risk-normal';
        } else {
            // For other risks, lower is better
            if (value > threshold.critical) return 'risk-critical';
            if (value > threshold.warning) return 'risk-warning';
            return 'risk-normal';
        }
    };

    if (loading) {
        return (
            <div className="bcbs-report-container loading-container">
                <div className="loading-spinner">
                    <i className="fas fa-spinner fa-spin"></i>
                    <p>Loading BCBS 239 Report...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bcbs-report-container error-container">
                <div className="error-message">
                    <i className="fas fa-exclamation-triangle"></i>
                    <p>{error}</p>
                    <button className="retry-btn" onClick={fetchBCBSData}>
                        <i className="fas fa-redo"></i> Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="bcbs-report-container">
            <h1>BCBS 239 Regulatory Report</h1>
            <div className="report-date">Reporting Date: {new Date(reportData.reporting_date).toLocaleDateString()}</div>
            
            <div className="report-summary">
                <div className="summary-box">
                    <h3>Total Capital Ratio</h3>
                    <div className="ratio-value">{getTotalCapitalRatio()}</div>
                    <div className={`status-indicator ${getCapitalStatus().toLowerCase()}`}>{getCapitalStatus()}</div>
                </div>
                
                <div className="summary-box">
                    <h3>Risk Profile</h3>
                    <div className="risk-chart">
                        {reportData.latest_metrics.map((metric) => (
                            <div 
                                key={metric.risk_type}
                                className="risk-bar"
                                style={{ 
                                    height: `${parseFloat(metric.value) * 5}px`,
                                    backgroundColor: riskInfo[metric.risk_type]?.color || '#999'
                                }}
                                title={`${formatRiskType(metric.risk_type)}: ${metric.value}%`}
                            />
                        ))}
                    </div>
                </div>
            </div>
            
            <div className="risk-summary-cards">
                <div className="summary-card">
                    <h3>Average Credit Risk</h3>
                    <div className="avg-value">{reportData.credit_risk_avg}%</div>
                    <p>Historical average across all reporting periods</p>
                </div>
                <div className="summary-card">
                    <h3>Average Market Risk</h3>
                    <div className="avg-value">{reportData.market_risk_avg}%</div>
                    <p>Historical average across all reporting periods</p>
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
                        {reportData.latest_metrics.map((metric) => (
                            <tr key={metric.risk_type}>
                                <td>{formatRiskType(metric.risk_type)}</td>
                                <td
                                    className="risk-value hover-effect"
                                    onMouseEnter={(e) => handleRiskHover(metric.risk_type, e)}
                                    onMouseLeave={handleMouseLeave}
                                    onClick={() => handleRiskClick(metric.risk_type)}
                                >
                                    {metric.value}%
                                </td>
                                <td>{metric.rwa ? `€${metric.rwa}M` : 'N/A'}</td>
                                <td className="trend-cell">
                                    {getTrendIcon(metric.trend)}
                                    {metric.trend}
                                </td>
                                <td>
                                    <Link to={`/risk-detail/${metric.risk_type}`} className="view-details-btn">
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
                    <h4>{formatRiskType(selectedRisk)}</h4>
                    <p>{riskInfo[selectedRisk]?.description || 'Risk information not available'}</p>
                    <div className="tooltip-sources">
                        <strong>Data Sources:</strong>
                        <ul>
                            {/* Use database sources if available, otherwise fall back to static data */}
                            {sourceData[selectedRisk] ? 
                                sourceData[selectedRisk].map((source, index) => (
                                    <li key={index}>{source.source} - {source.contribution}%</li>
                                ))
                                :
                                riskInfo[selectedRisk]?.sources.map((source, index) => (
                                    <li key={index}>{source}</li>
                                ))
                            }
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