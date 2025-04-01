import React, { useState, useEffect } from 'react';
import axios from 'axios';
import RiskDataLineageGraph from './RiskDataLineageGraph';
import './RiskLineagePage.css';

// Mock data for testing when API is not available
const MOCK_DATA = {
  market: {
    riskType: 'market',
    reportingDate: '2023-12-31',
    aggregatedValue: 15000000,
    nodes: [
      { id: 'market_risk', label: 'Market Risk', type: 'risk' },
      { id: 'trade_1', label: 'Trade #1234', type: 'transaction', details: { asset_class: 'Equity', counterparty: 'Bank A', notional_amount: 5000000, execution_timestamp: '2023-12-15T10:30:00Z' } },
      { id: 'trade_2', label: 'Trade #5678', type: 'transaction', details: { asset_class: 'Fixed Income', counterparty: 'Bank B', notional_amount: 7500000, execution_timestamp: '2023-12-20T14:45:00Z' } },
      { id: 'trade_3', label: 'Trade #9012', type: 'transaction', details: { asset_class: 'Derivatives', counterparty: 'Bank C', notional_amount: 3500000, execution_timestamp: '2023-12-18T09:15:00Z' } }
    ],
    links: [
      { source: 'trade_1', target: 'market_risk', percentage: 30, value: 5 },
      { source: 'trade_2', target: 'market_risk', percentage: 45, value: 7 },
      { source: 'trade_3', target: 'market_risk', percentage: 25, value: 4 }
    ]
  },
  credit: {
    riskType: 'credit',
    reportingDate: '2023-12-31',
    aggregatedValue: 22000000,
    nodes: [
      { id: 'credit_risk', label: 'Credit Risk', type: 'risk' },
      { id: 'trade_4', label: 'Trade #3456', type: 'transaction', details: { asset_class: 'Loan', counterparty: 'Corp X', notional_amount: 8000000, execution_timestamp: '2023-12-10T11:20:00Z' } },
      { id: 'trade_5', label: 'Trade #7890', type: 'transaction', details: { asset_class: 'Bond', counterparty: 'Corp Y', notional_amount: 6500000, execution_timestamp: '2023-12-05T15:30:00Z' } },
      { id: 'trade_6', label: 'Trade #1234', type: 'transaction', details: { asset_class: 'Credit Default Swap', counterparty: 'Bank D', notional_amount: 9500000, execution_timestamp: '2023-12-22T10:45:00Z' } }
    ],
    links: [
      { source: 'trade_4', target: 'credit_risk', percentage: 35, value: 6 },
      { source: 'trade_5', target: 'credit_risk', percentage: 25, value: 4 },
      { source: 'trade_6', target: 'credit_risk', percentage: 40, value: 7 }
    ]
  }
};

const RiskLineagePage = () => {
  const [activeRiskType, setActiveRiskType] = useState('market');
  const [useMockData, setUseMockData] = useState(true); // Default to mock data for safety
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backendStatus, setBackendStatus] = useState(null);
  
  // Check if backend is available when component mounts
  useEffect(() => {
    checkBackendStatus();
  }, []);
  
  // Function to check if backend API is accessible
  const checkBackendStatus = async () => {
    try {
      // Just a ping to see if backend is up
      const response = await axios.get('http://localhost:8000/health', { timeout: 2000 });
      if (response.status === 200) {
        setBackendStatus('available');
        console.log('Backend API is available');
      }
    } catch (err) {
      console.warn('Backend API is not available, using mock data', err);
      setBackendStatus('unavailable');
      setUseMockData(true); // Ensure we use mock data if backend is down
    }
  };
  
  // Use effect to fetch data when risk type changes
  useEffect(() => {
    fetchData();
  }, [activeRiskType, useMockData, backendStatus]);
  
  // Function to fetch data from API or use mock data
  const fetchData = async () => {
    setError(null);
    
    // If using mock data, simply set it
    if (useMockData) {
      console.log('Using mock data for', activeRiskType);
      setGraphData(MOCK_DATA[activeRiskType]);
      return;
    }
    
    // Only proceed with API call if backend is confirmed available
    if (backendStatus !== 'available') {
      console.warn('Backend not confirmed available, falling back to mock data');
      setGraphData(MOCK_DATA[activeRiskType]);
      return;
    }
    
    // Otherwise fetch from API
    setLoading(true);
    try {
      console.log(`Fetching ${activeRiskType} risk data from API`);
      const response = await axios.get(`http://localhost:8000/api/data-lineage/network/${activeRiskType}`, {
        timeout: 10000 // 10 second timeout
      });
      
      console.log('Received data from API:', response.data);
      
      // Validate data structure
      if (!response.data || !response.data.nodes || !response.data.links) {
        throw new Error('Invalid data structure received from the server');
      }
      
      // Check for common data issues
      if (response.data.nodes.length === 0) {
        console.warn('No nodes in response data');
      }
      
      setGraphData(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching data from API:', err);
      setError(`Failed to load ${activeRiskType} risk data: ${err.message}`);
      setLoading(false);
      
      // Fall back to mock data if real API fails
      console.log('Falling back to mock data due to API error');
      setGraphData(MOCK_DATA[activeRiskType]);
    }
  };
  
  // Toggle between mock and API data
  const toggleDataSource = () => {
    // If backend is unavailable and trying to switch to API, show warning
    if (backendStatus !== 'available' && useMockData) {
      setError('Backend API is not available. Using mock data instead.');
      setTimeout(() => setError(null), 3000);
      return;
    }
    
    setUseMockData(!useMockData);
  };
  
  return (
    <div className="risk-lineage-page">
      <header className="risk-lineage-header">
        <h1>Risk Data Lineage Visualization</h1>
        <div className="risk-type-selector">
          <button 
            className={`risk-type-btn ${activeRiskType === 'market' ? 'active' : ''}`}
            onClick={() => setActiveRiskType('market')}
          >
            Market Risk
          </button>
          <button 
            className={`risk-type-btn ${activeRiskType === 'credit' ? 'active' : ''}`}
            onClick={() => setActiveRiskType('credit')}
          >
            Credit Risk
          </button>
          <button
            className={`mock-toggle-btn ${backendStatus === 'unavailable' ? 'disabled' : ''}`}
            onClick={toggleDataSource}
            title={backendStatus === 'unavailable' ? 'Backend API unavailable' : ''}
          >
            {useMockData ? 'Using Mock Data' : 'Using API Data'}
            {backendStatus === 'unavailable' && ' (API Offline)'}
          </button>
          <button
            className="refresh-btn"
            onClick={fetchData}
            title="Refresh data"
          >
            <i className="fas fa-sync-alt"></i>
          </button>
        </div>
      </header>
      
      <main className="risk-lineage-content">
        {loading ? (
          <div className="graph-loading">
            <i className="fas fa-spinner fa-spin"></i>
            <span>Loading {activeRiskType} risk data lineage...</span>
          </div>
        ) : error ? (
          <div className="graph-error">
            <i className="fas fa-exclamation-triangle"></i>
            <span>{error}</span>
          </div>
        ) : (
          <RiskDataLineageGraph 
            riskType={activeRiskType} 
            graphData={graphData} 
          />
        )}
      </main>
      
      <footer className="risk-lineage-footer">
        <p>
          Visualizes the connections between aggregated risk values and the individual transactions that contribute to them.
          {useMockData && ' (Using sample data)'}
        </p>
      </footer>
    </div>
  );
};

export default RiskLineagePage; 