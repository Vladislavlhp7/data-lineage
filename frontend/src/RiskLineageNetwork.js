import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './RiskLineageNetwork.css';
import * as d3 from 'd3';

const RiskLineageNetwork = ({ riskType, onClose }) => {
  const [networkData, setNetworkData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  
  // Simulation references for d3
  const simulationRef = useRef(null);
  
  useEffect(() => {
    const fetchNetworkData = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`http://localhost:8000/api/data-lineage/network/${riskType}`);
        setNetworkData(response.data);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching network data:", err);
        setError(`Failed to load ${riskType} risk network: ${err.message}`);
        setLoading(false);
      }
    };
    
    fetchNetworkData();
    
    // Cleanup
    return () => {
      if (simulationRef.current) {
        simulationRef.current.stop();
      }
    };
  }, [riskType]);
  
  // Setup the network visualization when data is loaded
  useEffect(() => {
    if (!networkData || !svgRef.current) return;
    
    renderNetwork();
    
    // Window resize handler
    const handleResize = () => {
      renderNetwork();
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [networkData]);
  
  // Function to render the network visualization
  const renderNetwork = () => {
    if (!networkData || !svgRef.current || !containerRef.current) return;
    
    // Clear previous visualization
    d3.select(svgRef.current).selectAll("*").remove();
    
    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height);
    
    // Create svg groups for links and nodes
    const g = svg.append("g");
    const linksGroup = g.append("g").attr("class", "links");
    const nodesGroup = g.append("g").attr("class", "nodes");
    
    // Add zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });
    
    svg.call(zoom);
    
    // Central risk node should be at the center
    const nodes = networkData.nodes.map(node => ({
      ...node,
      x: node.type === 'risk' ? width / 2 : Math.random() * width,
      y: node.type === 'risk' ? height / 2 : Math.random() * height
    }));
    
    // Create links with source and target references
    const nodeById = new Map(nodes.map(node => [node.id, node]));
    const links = networkData.links.map(link => ({
      ...link,
      source: nodeById.get(link.source),
      target: nodeById.get(link.target),
      value: link.value || 1
    }));
    
    // Add links to the visualization
    const link = linksGroup.selectAll(".link")
      .data(links)
      .enter()
      .append("line")
      .attr("class", d => `link ${d.source.type}-${d.target.type}`)
      .attr("stroke-width", d => Math.max(1, Math.sqrt(d.value) / 5));
    
    // Add link labels for percentage contributions
    const linkLabel = linksGroup.selectAll(".link-label")
      .data(links.filter(l => l.percentage)) // Only links with percentage
      .enter()
      .append("text")
      .attr("class", "link-label")
      .attr("text-anchor", "middle")
      .attr("dy", -5)
      .text(d => `${d.percentage}%`);
    
    // Define node drag behavior
    const dragStarted = (event, d) => {
      if (!event.active) simulationRef.current.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    };
    
    const dragged = (event, d) => {
      d.fx = event.x;
      d.fy = event.y;
    };
    
    const dragEnded = (event, d) => {
      if (!event.active) simulationRef.current.alphaTarget(0);
      // If it's the risk node, keep it fixed at the current position
      if (d.type !== 'risk') {
        d.fx = null;
        d.fy = null;
      }
    };
    
    // Add nodes to the visualization
    const node = nodesGroup.selectAll(".node")
      .data(nodes)
      .enter()
      .append("g")
      .attr("class", d => `node ${d.type}`)
      .call(d3.drag()
        .on("start", dragStarted)
        .on("drag", dragged)
        .on("end", dragEnded))
      .on("click", (event, d) => {
        event.stopPropagation();
        setSelectedNode(d);
      });
    
    // Node circles
    node.append("circle")
      .attr("r", d => d.size || 10)
      .attr("class", d => `node-circle ${d.type}`)
      .attr("fill", d => getNodeColor(d.type));
    
    // Node labels
    node.append("text")
      .attr("dx", d => (d.size || 10) + 4)
      .attr("dy", 4)
      .attr("class", "node-label")
      .text(d => d.label);
    
    // Fix the central risk node position
    const riskNode = nodes.find(n => n.type === 'risk');
    if (riskNode) {
      riskNode.fx = width / 2;
      riskNode.fy = height / 2;
    }
    
    // Start the simulation
    simulationRef.current = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(d => {
        // Adjust link distance based on node types
        if (d.source.type === 'risk' || d.target.type === 'risk') {
          return 150; // Longer distance for links connected to risk node
        }
        return 80; // Normal distance for other links
      }))
      .force("charge", d3.forceManyBody().strength(d => {
        // Stronger repulsion for the risk node
        if (d.type === 'risk') return -500;
        return -100;
      }))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide().radius(d => (d.size || 10) + 10))
      .on("tick", () => {
        // Update link positions
        link
          .attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y);
        
        // Update link label positions
        linkLabel
          .attr("x", d => (d.source.x + d.target.x) / 2)
          .attr("y", d => (d.source.y + d.target.y) / 2);
        
        // Update node positions
        node
          .attr("transform", d => `translate(${d.x},${d.y})`);
      });
    
    // Add click handler on background to clear selection
    svg.on("click", () => {
      setSelectedNode(null);
    });
    
    // Center the view initially
    svg.call(zoom.transform, d3.zoomIdentity);
  };
  
  // Helper to get node color based on type
  const getNodeColor = (type) => {
    switch (type) {
      case 'risk': return 'var(--risk-color)';
      case 'transaction': return 'var(--transaction-color)';
      case 'validation': return 'var(--validation-color)';
      case 'enrichment': return 'var(--enrichment-color)';
      case 'risk_calculation': return 'var(--risk-calculation-color)';
      default: return '#999';
    }
  };
  
  // Render loading state
  if (loading) {
    return (
      <div className="risk-network-container">
        <div className="network-header">
          <h2>Loading {riskType ? riskType.charAt(0).toUpperCase() + riskType.slice(1) : ''} Risk Network...</h2>
          <button className="close-network-btn" onClick={onClose}>
            <i className="fas fa-times"></i>
          </button>
        </div>
        <div className="network-loading">
          <i className="fas fa-spinner fa-spin"></i> Loading network data...
        </div>
      </div>
    );
  }
  
  // Render error state
  if (error) {
    return (
      <div className="risk-network-container">
        <div className="network-header">
          <h2>Error Loading Network</h2>
          <button className="close-network-btn" onClick={onClose}>
            <i className="fas fa-times"></i>
          </button>
        </div>
        <div className="network-error">
          <i className="fas fa-exclamation-triangle"></i> {error}
        </div>
      </div>
    );
  }
  
  return (
    <div className="risk-network-container">
      <div className="network-header">
        <h2>{networkData?.riskType.charAt(0).toUpperCase() + networkData?.riskType.slice(1)} Risk Lineage Network</h2>
        <div className="network-meta">
          <span className="reporting-date">Reporting Date: {networkData?.reportingDate}</span>
          <span className="total-value">Total Value: ${networkData?.aggregatedValue.toLocaleString()}</span>
        </div>
        <button className="close-network-btn" onClick={onClose}>
          <i className="fas fa-times"></i>
        </button>
      </div>
      
      <div className="network-content">
        <div className="network-visualization" ref={containerRef}>
          <svg ref={svgRef}></svg>
        </div>
        
        <div className="network-sidebar">
          <div className="network-legend">
            <h3>Legend</h3>
            <div className="legend-item">
              <span className="legend-color risk"></span>
              <span className="legend-label">Risk Node</span>
            </div>
            <div className="legend-item">
              <span className="legend-color transaction"></span>
              <span className="legend-label">Transaction</span>
            </div>
            <div className="legend-item">
              <span className="legend-color validation"></span>
              <span className="legend-label">Validation</span>
            </div>
            <div className="legend-item">
              <span className="legend-color enrichment"></span>
              <span className="legend-label">Enrichment</span>
            </div>
            <div className="legend-item">
              <span className="legend-color risk_calculation"></span>
              <span className="legend-label">Risk Calculation</span>
            </div>
          </div>
          
          <div className="network-stats">
            <h3>Network Details</h3>
            <div className="stat-item">
              <span className="stat-label">Nodes:</span>
              <span className="stat-value">{networkData?.nodes.length || 0}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Links:</span>
              <span className="stat-value">{networkData?.links.length || 0}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Transactions:</span>
              <span className="stat-value">
                {networkData?.nodes.filter(n => n.type === 'transaction').length || 0}
              </span>
            </div>
          </div>
          
          {selectedNode && (
            <div className="node-details">
              <h3>{selectedNode.label}</h3>
              
              {selectedNode.type === 'transaction' && (
                <div className="node-properties">
                  <div className="node-property">
                    <span className="property-label">ID:</span>
                    <span className="property-value">{selectedNode.id}</span>
                  </div>
                  <div className="node-property">
                    <span className="property-label">Asset Class:</span>
                    <span className="property-value">{selectedNode.assetClass}</span>
                  </div>
                  <div className="node-property">
                    <span className="property-label">Counterparty:</span>
                    <span className="property-value">{selectedNode.counterparty}</span>
                  </div>
                  <div className="node-property">
                    <span className="property-label">Notional:</span>
                    <span className="property-value">${selectedNode.notional.toLocaleString()}</span>
                  </div>
                  <div className="node-property">
                    <span className="property-label">Risk Contribution:</span>
                    <span className="property-value">
                      ${selectedNode.riskContribution.toLocaleString()} ({selectedNode.percentage}%)
                    </span>
                  </div>
                </div>
              )}
              
              {selectedNode.type === 'risk' && (
                <div className="node-properties">
                  <div className="node-property">
                    <span className="property-label">Type:</span>
                    <span className="property-value">{selectedNode.label}</span>
                  </div>
                  <div className="node-property">
                    <span className="property-label">Total Value:</span>
                    <span className="property-value">${selectedNode.value.toLocaleString()}</span>
                  </div>
                </div>
              )}
              
              {['validation', 'enrichment', 'risk_calculation'].includes(selectedNode.type) && 
               selectedNode.details && (
                <div className="node-properties">
                  {Object.entries(selectedNode.details).map(([key, value]) => (
                    <div className="node-property" key={key}>
                      <span className="property-label">{key.replace(/_/g, ' ')}:</span>
                      <span className="property-value">
                        {typeof value === 'number' ? value.toLocaleString() : 
                         value === null ? 'N/A' : value.toString()}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              
              <button className="clear-selection-btn" onClick={() => setSelectedNode(null)}>
                <i className="fas fa-times"></i> Clear Selection
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RiskLineageNetwork; 