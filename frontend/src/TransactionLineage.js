import React, { useState, useEffect, useRef } from 'react';
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
  
  // State for draggable visualization
  const [isDragging, setIsDragging] = useState(false);
  const [dragPosition, setDragPosition] = useState({ x: 0, y: 0 });
  const [startPosition, setStartPosition] = useState({ x: 0, y: 0 });
  const visualizationRef = useRef(null);
  
  // State for minimizable data panel
  const [isDataPanelMinimized, setIsDataPanelMinimized] = useState(false);
  const [dataPanelPosition, setDataPanelPosition] = useState({ x: 0, y: 0 });
  const [isDraggingPanel, setIsDraggingPanel] = useState(false);
  const [panelStartPosition, setPanelStartPosition] = useState({ x: 0, y: 0 });
  const dataPanelRef = useRef(null);
  
  // Add state for visualization scale
  const [scale, setScale] = useState(1);
  
  // Fetch transaction steps and initialize a transaction
  useEffect(() => {
    const initializeTransaction = async () => {
      setLoading(true);
      try {
        // Fetch transaction steps from the backend
        const stepsResponse = await axios.get('http://localhost:8000/transaction/steps');
        setSteps(stepsResponse.data);
        
        // Initialize a new transaction
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

  // Reset the simulation
  const resetSimulation = async () => {
    if (!transactionId) {
      alert('No transaction found to reset.');
      return;
    }
    setLoading(true);
    try {
      const response = await axios.get(`http://localhost:8000/transaction/${transactionId}/reset`);
      setTransactionData(response.data.data); // Reset transaction data
      setCurrentStep(0); // Reset to the first step
      setTransformations([]); // Clear transformations
      setProcessingAnimation(false); // Stop any ongoing animations
      setDragPosition({ x: 0, y: 0 }); // Reset drag position
    } catch (error) {
      console.error('Error resetting transaction:', error);
      alert('Failed to reset transaction. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Mouse event handlers for dragging the background visualization
  const handleMouseDown = (e) => {
    // Check if we're clicking on the panel or a control element
    if (e.target.closest('.floating-data-panel, .header-actions, .transaction-id') || 
        e.target.tagName === 'BUTTON') {
      return;
    }
    setIsDragging(true);
    setStartPosition({
      x: e.clientX - dragPosition.x,
      y: e.clientY - dragPosition.y
    });
  };
  
  const handleMouseMove = (e) => {
    if (isDragging) {
      const newX = e.clientX - startPosition.x;
      const newY = e.clientY - startPosition.y;
      
      setDragPosition({ x: newX, y: newY });
    } else if (isDraggingPanel) {
      const newX = e.clientX - panelStartPosition.x;
      const newY = e.clientY - panelStartPosition.y;
      
      setDataPanelPosition({ x: newX, y: newY });
    }
  };
  
  const handleMouseUp = () => {
    setIsDragging(false);
    setIsDraggingPanel(false);
  };
  
  const handleMouseLeave = () => {
    setIsDragging(false);
    setIsDraggingPanel(false);
  };
  
  // Mouse event handlers for dragging the data panel
  const handlePanelMouseDown = (e) => {
    if (!e.target.closest('.panel-header')) return;
    
    e.stopPropagation();
    setIsDraggingPanel(true);
    setPanelStartPosition({
      x: e.clientX - dataPanelPosition.x,
      y: e.clientY - dataPanelPosition.y
    });
  };
  
  // Toggle data panel minimized state
  const toggleDataPanel = () => {
    setIsDataPanelMinimized(!isDataPanelMinimized);
  };

  // Function to handle zoom in/out
  const handleZoom = (zoomIn) => {
    if (zoomIn) {
      // Zoom in - increase scale by 0.1, max 2.0
      setScale(prevScale => Math.min(prevScale + 0.1, 2.0));
    } else {
      // Zoom out - decrease scale by 0.1, min 0.5
      setScale(prevScale => Math.max(prevScale - 0.1, 0.5));
    }
  };
  
  // Reset zoom to default scale
  const resetZoom = () => {
    setScale(1);
  };

  // Function to center the lineage visualization
  const centerVisualization = () => {
    setDragPosition({ x: 0, y: 0 }); // Reset to the origin
  };

  // Enable scrolling with the mouse pad
  const handleWheel = (e) => {
    if (e.ctrlKey) {
      // Zoom in/out with Ctrl + Scroll
      handleZoom(e.deltaY < 0);
    } else {
      // Scroll the view
      setDragPosition((prev) => ({
        x: prev.x - e.deltaX,
        y: prev.y - e.deltaY,
      }));
    }
  };

  useEffect(() => {
    // Center the visualization on initial load
    centerVisualization();
  }, [visualizationRef]);

  // Function to create a new transaction
  const createTransaction = async () => {
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/api/transaction/create');
      const tradeExecutionData = response.data.initial_data.trade_execution; // Extract nested data
      setTransactionId(response.data.trade_id);
      setTransactionData(response.data.initial_data); // Populate the entire transaction data
      setCurrentStep(0); // Reset currentStep to 0 for the new transaction
      setTransformations([]); // Clear transformations
      localStorage.setItem('transactionId', response.data.trade_id); // Store in browser
      localStorage.setItem('transactionData', JSON.stringify(response.data.initial_data));
    } catch (error) {
      console.error('Error creating transaction:', error);
      alert('Failed to create transaction. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Function to promote the transaction to the next stage
  const promoteTransaction = async () => {
    if (!transactionId) {
      alert('No transaction found. Please start a transaction first.');
      return;
    }
    setProcessingAnimation(true); // Start the animation
    try {
      const response = await axios.post(`http://localhost:8000/api/transaction/promote/${transactionId}`);
      const updatedData = response.data.updated_data;

      // Update transaction data with the latest data for all stages
      setTransactionData({
        tradeExecution: updatedData.trade_execution,
        tradeValidation: updatedData.trade_validation,
        tradeEnrichment: updatedData.trade_enrichment,
        riskCalculation: updatedData.risk_calculation,
        settlementPreparation: updatedData.settlement_preparation,
        regulatoryReporting: updatedData.regulatory_reporting,
      });

      // Mark the current step as completed and move to the next step
      setTimeout(() => {
        setCurrentStep((prevStep) => prevStep + 1);
        setProcessingAnimation(false); // Stop the animation
      }, 1000); // Match the animation duration
    } catch (error) {
      console.error('Error promoting transaction:', error);
      alert('Failed to promote transaction. Please try again.');
      setProcessingAnimation(false); // Stop the animation on error
    }
  };

  // Load transaction from browser storage on component mount
  useEffect(() => {
    const storedTransactionId = localStorage.getItem('transactionId');
    const storedTransactionData = localStorage.getItem('transactionData');
    if (storedTransactionId && storedTransactionData) {
      setTransactionId(storedTransactionId);
      setTransactionData(JSON.parse(storedTransactionData));
    }
  }, []);

  if (loading) {
    return <div className="loading"><i className="fas fa-spinner fa-spin"></i> Loading transaction data...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  const currentStepData = steps[currentStep] || {};

  // Ensure proper rendering of transaction steps
  const renderTransactionSteps = () => {
    return steps.map((step, index) => (
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
          <div className={`flow-connector ${index < currentStep ? 'completed' : ''}`}>
            <div className="connector-line"></div>
            {processingAnimation && index === currentStep && (
              <div className="moving-point"></div> // Add the moving point
            )}
          </div>
        )}
      </React.Fragment>
    ));
  };

  // Render transformations in the data panel
  const renderTransformations = () => {
    return transformations.map((transformation, index) => (
      <div key={index} className="transformation-item">
        <div className={`transform-type ${transformation.action}`}>
          {transformation.action}
        </div>
        <div className="transform-field">{transformation.field}</div>
        <div className="transform-description">{transformation.description}</div>
      </div>
    ));
  };

  // Render the transaction data in the data panel
  const renderTransactionData = () => {
    if (!transactionData) return null;

    const sections = [
      { title: "Trade Execution", data: transactionData.tradeExecution },
      { title: "Trade Validation", data: transactionData.tradeValidation },
      { title: "Trade Enrichment", data: transactionData.tradeEnrichment },
      { title: "Risk Calculation", data: transactionData.riskCalculation },
      { title: "Settlement Preparation", data: transactionData.settlementPreparation },
      { title: "Regulatory Reporting", data: transactionData.regulatoryReporting },
    ];

    return sections.map((section, index) => (
      section.data && (
        <div key={index} className="transaction-section">
          <h4>{section.title}</h4>
          <table>
            <tbody>
              {Object.entries(section.data).map(([key, value]) => (
                <tr key={key}>
                  <td>{key}</td>
                  <td>{value !== null ? value.toString() : "N/A"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )
    ));
  };

  // Replace the "Transaction Data" panel with the transaction table
  return (
    <div 
      className="transaction-lineage full-width"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseLeave}
      onWheel={handleWheel} // Enable scrolling with the mouse pad
    >
      {/* Main playground background with visualization */}
      <div className="lineage-playground" onMouseDown={handleMouseDown}>
        <div 
          className="visualization-content"
          ref={visualizationRef}
          style={{
            transform: `translate(${dragPosition.x}px, ${dragPosition.y}px) scale(${scale})`,
            transformOrigin: 'center center',
            cursor: isDragging ? 'grabbing' : 'grab',
          }}
        >
          <div className="flow-section">
            <div className="section-label">Transaction Process Flow</div>
            <div className="transaction-flow">{renderTransactionSteps()}</div>
          </div>
          {/* Lower Section - Data Lineage Graph */}
          <div className="lineage-section">
            <div className="section-label">Data Lineage Graph</div>
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
              
              {/* Trade Enrichment */}
              <div className={`lineage-node process ${currentStep >= 2 ? 'active' : ''}`}>
                <div className="node-icon"><i className="fas fa-plus-circle"></i></div>
                <div className="node-text">Trade Enrichment</div>
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
              <div className={`lineage-node process ${currentStep >= 5 ? 'active' : ''}`}>
                <div className="node-icon"><i className="fas fa-clipboard-list"></i></div>
                <div className="node-text">Regulatory Reporting</div>
              </div>
              <div className="lineage-connector"></div>
              
              {/* Regulatory Report */}
              <div className={`lineage-node target ${currentStep >= 5 ? 'active' : ''}`}>
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
        
        {/* Add zoom controls */}
        <div className="zoom-controls">
          <button onClick={() => handleZoom(true)} className="zoom-btn" title="Zoom In">
            <i className="fas fa-search-plus"></i>
          </button>
          <button onClick={resetZoom} className="zoom-btn" title="Reset Zoom">
            <i className="fas fa-expand"></i> {Math.round(scale * 100)}%
          </button>
          <button onClick={() => handleZoom(false)} className="zoom-btn" title="Zoom Out">
            <i className="fas fa-search-minus"></i>
          </button>
        </div>
        
        {/* Reset position button */}
        <button 
          className="reset-position-btn"
          onClick={centerVisualization}
        >
          <i className="fas fa-crosshairs"></i> Reset Position
        </button>
      </div>
      
      {/* Fixed Header Controls */}
      <div className="fixed-header under-main-banner">
        <div className="header-content">
          <h1>Transaction Lineage Simulation</h1>
          <div className="header-controls">
            <button onClick={createTransaction} disabled={loading} className="start-btn">
              {loading ? 'Starting...' : 'Start Transaction'}
            </button>
            {currentStep < steps.length - 1 ? (
              <button 
                className="next-step-btn" 
                onClick={promoteTransaction}
                disabled={processingAnimation || !transactionId}
              >
                {processingAnimation ? (
                  <><i className="fas fa-spinner fa-spin"></i> Processing...</>
                ) : (
                  <>Process to Next Step <i className="fas fa-arrow-right"></i></>
                )}
              </button>
            ) : (
              <div className="completion-badge">
                <i className="fas fa-check-circle"></i>
                <span>Completed</span>
              </div>
            )}
            <button onClick={resetSimulation} className="reset-btn">
              <i className="fas fa-redo"></i> Reset
            </button>
          </div>
        </div>
      </div>
      
      {/* Replace "Transaction Data" panel with the transaction table */}
      <div 
        className={`floating-data-panel vertical-panel ${isDataPanelMinimized ? 'minimized' : ''}`}
        style={{
          transform: `translateY(${dataPanelPosition.y}px)`
        }}
        ref={dataPanelRef}
        onMouseDown={handlePanelMouseDown}
      >
        <div className="panel-header">
          <h3>Transaction Data</h3>
          <div className="panel-controls">
            <button 
              className="minimize-btn"
              onClick={toggleDataPanel}
              title={isDataPanelMinimized ? "Expand" : "Minimize"}
            >
              <i className={`fas fa-${isDataPanelMinimized ? 'chevron-left' : 'chevron-right'}`}></i>
            </button>
          </div>
        </div>
        
        {!isDataPanelMinimized && (
          <div className="panel-body">
            <div className="transaction-table">
              {renderTransactionData()}
            </div>

            {/* Render transformations */}
            {transformations.length > 0 && (
              <div className="transformations">
                <h4>Transformations</h4>
                <div className="transformation-list">
                  {renderTransformations()}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default TransactionLineage;
