import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import './TransactionLineage.css';

function TransactionLineage() {
  const [transactionId, setTransactionId] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [steps, setSteps] = useState([]);
  const [transactionData, setTransactionData] = useState(null);
  const [transformations, setTransformations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processingAnimation, setProcessingAnimation] = useState(false);

  // Fetch transaction steps and initialize a transaction
  useEffect(() => {
    const initializeTransaction = async () => {
      setLoading(true);
      try {
        // First get all steps
        const stepsResponse = await axios.get('http://localhost:8000/transaction/steps');
        setSteps(stepsResponse.data);
        
        // Then initialize a new transaction
        const initResponse = await axios.get('http://localhost:8000/transaction/init');
        setTransactionId(initResponse.data.transaction_id);
        setTransactionData(initResponse.data.initial_data);
        setCurrentStep(0);
        setLoading(false);
      } catch (error) {
        console.error('Error initializing transaction:', error);
        setError('Failed to initialize transaction simulation');
        setLoading(false);
      }
    };

    initializeTransaction();
  }, []);

  // Process the transaction to the next step
  const processStep = async () => {
    if (currentStep >= steps.length - 1) return;
    
    setProcessingAnimation(true);
    
    try {
      // Call the process endpoint with current step
      const response = await axios.get(`http://localhost:8000/transaction/${transactionId}/process?step_index=${currentStep}`);
      
      // Update the state with the response data
      setTransactionData(response.data.current_data);
      setCurrentStep(currentStep + 1);
      setTransformations(response.data.transformations);
      
      // Use a short timeout to show animation
      setTimeout(() => {
        setProcessingAnimation(false);
      }, 1000);
    } catch (error) {
      console.error('Error processing transaction step:', error);
      setError('Failed to process transaction step');
      setProcessingAnimation(false);
    }
  };

  // Reset the simulation
  const resetSimulation = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:8000/transaction/${transactionId}/reset`);
      setTransactionData(response.data.data);
      setCurrentStep(0);
      setTransformations([]);
      setLoading(false);
    } catch (error) {
      console.error('Error resetting transaction:', error);
      setError('Failed to reset transaction');
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading"><i className="fas fa-spinner fa-spin"></i> Loading transaction data...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  const currentStepData = steps[currentStep] || {};

  return (
    <div className="transaction-lineage">
      <div className="header-actions">
        <Link to="/" className="back-link">
          <i className="fas fa-arrow-left"></i> Back to Home
        </Link>
        <h1>Transaction Lineage Simulation</h1>
        <button onClick={resetSimulation} className="reset-btn">
          <i className="fas fa-redo"></i> Reset
        </button>
      </div>

      {/* Transaction ID display */}
      <div className="transaction-id">
        <span className="label">Transaction ID:</span>
        <span className="value">{transactionId}</span>
      </div>

      {/* Transaction flow visual representation */}
      <div className="transaction-flow">
        {steps.map((step, index) => (
          <React.Fragment key={step.id}>
            <div 
              className={`flow-node ${index === currentStep ? 'active' : ''} ${index < currentStep ? 'completed' : ''}`}
              title={step.description}
            >
              <div className="node-content">
                <div className="node-icon">
                  {index < currentStep ? (
                    <i className="fas fa-check"></i>
                  ) : (
                    <span className="step-number">{index + 1}</span>
                  )}
                </div>
                <div className="node-label">
                  <div className="step-name">{step.name}</div>
                  <div className="department">{step.department}</div>
                </div>
              </div>
            </div>
            {index < steps.length - 1 && (
              <div className={`flow-connector ${index < currentStep ? 'completed' : ''} ${processingAnimation && index === currentStep ? 'processing' : ''}`}>
                <div className="connector-line"></div>
                {processingAnimation && index === currentStep && (
                  <div className="processing-animation">
                    <i className="fas fa-circle"></i>
                  </div>
                )}
              </div>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Current step information */}
      <div className="current-step-info">
        <h2>{currentStepData.name}</h2>
        <div className="department-badge">{currentStepData.department}</div>
        <p className="step-description">{currentStepData.description}</p>
      </div>

      {/* Data transformation visualization */}
      <div className="data-transformation">
        <div className="data-panel">
          <h3>Transaction Data</h3>
          <div className="data-table">
            <table>
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Value</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {transactionData && Object.entries(transactionData).map(([key, value]) => {
                  // Determine if this field was transformed in the current step
                  const isNewField = transformations && transformations.some(
                    t => t.field === key && (t.action === 'added' || t.action === 'renamed')
                  );
                  
                  return (
                    <tr key={key} className={isNewField ? 'highlight-row' : ''}>
                      <td>{key}</td>
                      <td>
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </td>
                      <td>
                        {isNewField && (
                          <span className="status-badge new">
                            {transformations.find(t => t.field === key)?.action || 'New'}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Transformations list for current step */}
        {transformations && transformations.length > 0 && (
          <div className="transformations">
            <h3>Transformations in this Step</h3>
            <ul className="transformation-list">
              {transformations.map((transform, idx) => (
                <li key={idx} className="transformation-item">
                  <span className={`transform-type ${transform.action}`}>
                    {transform.action === 'added' ? 'Add Field' : 
                    transform.action === 'renamed' ? 'Rename Field' : 
                    transform.action === 'modified' ? 'Modify Field' : 'Transform'}
                  </span>
                  <span className="transform-field">{transform.field}</span>
                  <span className="transform-description">{transform.description}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Bottom action area */}
      <div className="action-area">
        {currentStep < steps.length - 1 ? (
          <button 
            className="next-step-btn" 
            onClick={processStep}
            disabled={processingAnimation}
          >
            {processingAnimation ? (
              <><i className="fas fa-spinner fa-spin"></i> Processing...</>
            ) : (
              <>Process to Next Step <i className="fas fa-arrow-right"></i></>
            )}
          </button>
        ) : (
          <div className="completion-message">
            <i className="fas fa-check-circle"></i>
            <span>Transaction processing complete!</span>
            <button onClick={resetSimulation} className="restart-btn">
              <i className="fas fa-redo"></i> Start New Transaction
            </button>
          </div>
        )}
      </div>

      {/* Data lineage graph visualization */}
      <div className="data-lineage-graph">
        <h3>Data Lineage Graph</h3>
        <div className="graph-container">
          <div className="graph-legend">
            <div className="legend-item">
              <div className="legend-color data-source"></div>
              <span>Data Source</span>
            </div>
            <div className="legend-item">
              <div className="legend-color process"></div>
              <span>Process</span>
            </div>
            <div className="legend-item">
              <div className="legend-color data-field"></div>
              <span>Data Field</span>
            </div>
            <div className="legend-item">
              <div className="legend-color target"></div>
              <span>Target System</span>
            </div>
          </div>
          
          <div className="graph-visualization">
            <div className="lineage-graph">
              {/* Trading System Source */}
              <div className="lineage-node source">
                <div className="node-icon"><i className="fas fa-database"></i></div>
                <div className="node-text">Trading System</div>
              </div>
              <div className="lineage-connector"></div>
              
              {/* Trade Capture */}
              <div className={`lineage-node process ${currentStep >= 0 ? 'active' : ''}`}>
                <div className="node-icon"><i className="fas fa-exchange-alt"></i></div>
                <div className="node-text">Trade Capture</div>
              </div>
              <div className="lineage-connector"></div>
              
              {/* Basic Trade Data */}
              <div className={`lineage-node data-field ${currentStep >= 0 ? 'active' : ''}`}>
                <div className="node-icon"><i className="fas fa-file-alt"></i></div>
                <div className="node-text">Basic Trade Data</div>
                <div className="node-details">
                  {currentStep >= 0 && (
                    <ul className="field-list">
                      <li>tradeId</li>
                      <li>clientId</li>
                      <li>securityId</li>
                      <li>quantity</li>
                      <li>price</li>
                    </ul>
                  )}
                </div>
              </div>
              <div className="lineage-connector"></div>
              
              {/* Trade Validation */}
              <div className={`lineage-node process ${currentStep >= 1 ? 'active' : ''}`}>
                <div className="node-icon"><i className="fas fa-check-circle"></i></div>
                <div className="node-text">Trade Validation</div>
              </div>
              <div className="lineage-connector"></div>
              
              {/* Validated Trade Data */}
              <div className={`lineage-node data-field ${currentStep >= 1 ? 'active' : ''}`}>
                <div className="node-icon"><i className="fas fa-file-alt"></i></div>
                <div className="node-text">Validated Trade</div>
                <div className="node-details">
                  {currentStep >= 1 && (
                    <ul className="field-list">
                      <li className="added">validationStatus</li>
                      <li className="added">validationTimestamp</li>
                    </ul>
                  )}
                </div>
              </div>
              <div className="lineage-connector"></div>
              
              {/* Trade Enrichment */}
              <div className={`lineage-node process ${currentStep >= 2 ? 'active' : ''}`}>
                <div className="node-icon"><i className="fas fa-plus-circle"></i></div>
                <div className="node-text">Trade Enrichment</div>
              </div>
              
              {/* External Market Data */}
              <div className={`lineage-node source side-input ${currentStep >= 2 ? 'active' : ''}`}>
                <div className="node-icon"><i className="fas fa-chart-line"></i></div>
                <div className="node-text">Market Data</div>
                <div className="side-connector"></div>
              </div>
              
              <div className="lineage-connector"></div>
              
              {/* Enriched Trade Data */}
              <div className={`lineage-node data-field ${currentStep >= 2 ? 'active' : ''}`}>
                <div className="node-icon"><i className="fas fa-file-alt"></i></div>
                <div className="node-text">Enriched Trade</div>
                <div className="node-details">
                  {currentStep >= 2 && (
                    <ul className="field-list">
                      <li className="added">securityName</li>
                      <li className="added">marketValue</li>
                      <li className="added">currency</li>
                      <li className="added">settlementDate</li>
                    </ul>
                  )}
                </div>
              </div>
              <div className="lineage-connector"></div>
              
              {/* Risk Calculation */}
              <div className={`lineage-node process ${currentStep >= 3 ? 'active' : ''}`}>
                <div className="node-icon"><i className="fas fa-chart-bar"></i></div>
                <div className="node-text">Risk Calculation</div>
              </div>
              <div className="lineage-connector"></div>
              
              {/* Risk Metrics */}
              <div className={`lineage-node data-field ${currentStep >= 3 ? 'active' : ''}`}>
                <div className="node-icon"><i className="fas fa-file-alt"></i></div>
                <div className="node-text">Risk Metrics</div>
                <div className="node-details">
                  {currentStep >= 3 && (
                    <ul className="field-list">
                      <li className="added">varValue</li>
                      <li className="added">deltaValue</li>
                      <li className="added">gammaValue</li>
                    </ul>
                  )}
                </div>
              </div>
              <div className="lineage-connector"></div>
              
              {/* Settlement Preparation */}
              <div className={`lineage-node process ${currentStep >= 4 ? 'active' : ''}`}>
                <div className="node-icon"><i className="fas fa-money-check-alt"></i></div>
                <div className="node-text">Settlement</div>
              </div>
              <div className="lineage-connector"></div>
              
              {/* Settlement Instructions */}
              <div className={`lineage-node data-field ${currentStep >= 4 ? 'active' : ''}`}>
                <div className="node-icon"><i className="fas fa-file-alt"></i></div>
                <div className="node-text">Settlement Instructions</div>
                <div className="node-details">
                  {currentStep >= 4 && (
                    <ul className="field-list">
                      <li className="renamed">valueCurrency</li>
                      <li className="added">settlementCurrency</li>
                      <li className="added">settlementInstructions</li>
                      <li className="added">accountDetails</li>
                    </ul>
                  )}
                </div>
              </div>
              <div className="lineage-connector"></div>
              
              {/* Regulatory Reporting */}
              <div className={`lineage-node process ${currentStep >= 5 ? 'active' : ''}`}></div>
                <div className="node-icon"><i className="fas fa-clipboard-list"></i></div>
                <div className="node-text">Regulatory Reporting</div>
              </div>
              <div className="lineage-connector"></div>
              
              {/* Regulatory Report */}
              <div className={`lineage-node target ${currentStep >= 5 ? 'active' : ''}`}></div>
                <div className="node-icon"><i className="fas fa-file-contract"></i></div>
                <div className="node-text">Regulatory Report</div>
                <div className="node-details">
                  {currentStep >= 5 && (
                    <ul className="field-list">
                      <li className="added">securityType</li>
                      <li className="added">tradingDesk</li>
                      <li className="added">reportingStatus</li>
                      <li className="added">regulatoryId</li>
                    </ul>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
  );
}

export default TransactionLineage;
