import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import * as d3 from 'd3';
import './RiskDataLineageGraph.css';

const RiskDataLineageGraph = ({ riskType = 'market', graphData = null }) => {
  const [selectedNode, setSelectedNode] = useState(null);
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  
  // Force simulation reference
  const simulationRef = useRef(null);

  // Use effect to render graph when data is available
  useEffect(() => {
    if (!graphData || !svgRef.current) {
      console.log('No graph data or SVG ref yet, skipping render');
      return;
    }
    
    console.log('Graph data available, rendering graph with', 
                graphData.nodes?.length || 0, 'nodes and', 
                graphData.links?.length || 0, 'links');
    renderGraph();
    
    const handleResize = () => {
      console.log('Window resized, re-rendering graph');
      renderGraph();
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [graphData]);
  
  const renderGraph = () => {
    if (!graphData || !svgRef.current || !containerRef.current) {
      console.log('Missing requirements for rendering:', {
        graphData: !!graphData,
        svgRef: !!svgRef.current,
        containerRef: !!containerRef.current
      });
      return;
    }
    
    console.log('Starting to render graph');
    
    // If the simulation is running, stop it
    if (simulationRef.current) {
      simulationRef.current.stop();
    }
    
    // Clear previous visualization
    d3.select(svgRef.current).selectAll("*").remove();
    
    const container = containerRef.current;
    const width = container.clientWidth || 800; // Fallback width
    const height = container.clientHeight || 500; // Fallback height
    
    console.log('Container dimensions:', { width, height });
    
    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height);
    
    // Create main group for zooming
    const g = svg.append("g");
    
    // Add zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });
    
    svg.call(zoom);
    
    // Create groups for links and nodes
    const linksGroup = g.append("g").attr("class", "links");
    const nodesGroup = g.append("g").attr("class", "nodes");
    
    // Process data - check for valid format and normalize if necessary
    if (!graphData.nodes || !graphData.links) {
      console.error('Invalid graph data structure:', graphData);
      return;
    }
    
    // Normalize node data if needed
    const normalizedNodes = graphData.nodes.map(node => {
      // Default type to transaction if not specified
      if (!node.type) {
        console.warn(`Node missing type, defaulting to transaction:`, node);
        node.type = 'transaction';
      }
      
      // Ensure ID exists
      if (!node.id) {
        console.warn(`Node missing id, generating one:`, node);
        node.id = `node_${Math.random().toString(36).substr(2, 9)}`;
      }
      
      return {
        ...node,
        // Set initial positions for force-directed layout
        x: node.type === 'risk' ? width / 2 : Math.random() * width,
        y: node.type === 'risk' ? height / 3 : Math.random() * height
      };
    });
    
    // Create lookup map for nodes by ID
    const nodeById = new Map(normalizedNodes.map(node => [node.id, node]));
    
    // Log missing nodes in links
    const missingNodeIds = new Set();
    graphData.links.forEach(link => {
      if (typeof link.source === 'object' && link.source !== null) {
        if (!link.source.id) {
          console.warn('Link source is an object without id:', link);
        }
      } else if (typeof link.source === 'string' && !nodeById.has(link.source)) {
        missingNodeIds.add(link.source);
      }
      
      if (typeof link.target === 'object' && link.target !== null) {
        if (!link.target.id) {
          console.warn('Link target is an object without id:', link);
        }
      } else if (typeof link.target === 'string' && !nodeById.has(link.target)) {
        missingNodeIds.add(link.target);
      }
    });
    
    if (missingNodeIds.size > 0) {
      console.error('Links reference missing nodes:', Array.from(missingNodeIds));
    }
    
    // Normalize links and filter out invalid ones
    const normalizedLinks = graphData.links
      .filter(link => {
        // Filter out links with missing source or target
        const sourceExists = typeof link.source === 'object' ? !!link.source : nodeById.has(link.source);
        const targetExists = typeof link.target === 'object' ? !!link.target : nodeById.has(link.target);
        
        if (!sourceExists || !targetExists) {
          console.warn('Filtering out link with missing node:', link);
          return false;
        }
        return true;
      })
      .map(link => {
        // Convert string IDs to node objects
        const sourceNode = typeof link.source === 'object' ? link.source : nodeById.get(link.source);
        const targetNode = typeof link.target === 'object' ? link.target : nodeById.get(link.target);
        
        return {
          ...link,
          source: sourceNode,
          target: targetNode,
          value: link.value || 1
        };
      });
    
    // If no valid nodes or links, show error
    if (normalizedNodes.length === 0 || normalizedLinks.length === 0) {
      console.error('No valid nodes or links to render', { 
        nodeCount: normalizedNodes.length, 
        linkCount: normalizedLinks.length 
      });
      
      // Add error message to SVG
      svg.append("text")
        .attr("class", "graph-error-text")
        .attr("x", width / 2)
        .attr("y", height / 2)
        .attr("text-anchor", "middle")
        .attr("fill", "#e63946")
        .text("Error: Invalid or empty graph data");
        
      return;
    }
    
    console.log('Creating visualization with', normalizedNodes.length, 'nodes and', normalizedLinks.length, 'links');
    
    // Add links to the visualization
    const link = linksGroup.selectAll(".link")
      .data(normalizedLinks)
      .enter()
      .append("line")
      .attr("class", d => `link ${d.source.type}-${d.target.type}`)
      .attr("stroke-width", d => Math.max(1, Math.sqrt(d.value) / 2));
    
    // Add link labels for percentage contributions
    const linkLabel = linksGroup.selectAll(".link-label")
      .data(normalizedLinks.filter(l => l.percentage))
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
      // If it's the risk node, keep it fixed
      if (d.type !== 'risk') {
        d.fx = null;
        d.fy = null;
      }
    };
    
    // Add nodes to the visualization
    const node = nodesGroup.selectAll(".node")
      .data(normalizedNodes)
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
    
    // Node circles with icons
    node.append("circle")
      .attr("r", d => getNodeSize(d.type))
      .attr("class", d => `node-circle ${d.type}`);
    
    // Add an icon to each node
    node.append("text")
      .attr("class", "node-icon")
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "central")
      .text(d => getNodeIcon(d.type));
    
    // Node labels
    node.append("text")
      .attr("class", "node-label")
      .attr("dx", d => (d.type === 'risk' ? 0 : getNodeSize(d.type) + 8))
      .attr("dy", d => (d.type === 'risk' ? -getNodeSize(d.type) - 8 : 4))
      .attr("text-anchor", d => (d.type === 'risk' ? "middle" : "start"))
      .text(d => d.label || d.id);
    
    // Fix the risk node position
    const riskNode = normalizedNodes.find(n => n.type === 'risk');
    if (riskNode) {
      riskNode.fx = width / 2;
      riskNode.fy = height / 3;
    } else {
      console.warn('No risk node found in data');
    }
    
    // Custom force configuration for risk lineage visualization
    simulationRef.current = d3.forceSimulation(normalizedNodes)
      .force("link", d3.forceLink(normalizedLinks).id(d => d.id).distance(d => {
        // Risk node should be central with transactions around it
        if (d.source.type === 'risk' || d.target.type === 'risk') {
          return 150;
        }
        // Transactions connect to validations, etc. at shorter distances
        return 80;
      }))
      .force("charge", d3.forceManyBody().strength(d => {
        // Risk node has stronger repulsion
        if (d.type === 'risk') return -800;
        if (d.type === 'transaction') return -300;
        return -150;
      }))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(d => getNodeSize(d.type) + 15))
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
    
    // Add legend for node types
    const legend = svg.append("g")
      .attr("class", "legend")
      .attr("transform", `translate(20, ${height - 150})`);
    
    const legendData = [
      { type: 'risk', label: 'Aggregated Risk' },
      { type: 'transaction', label: 'Transaction' },
      { type: 'validation', label: 'Validation' },
      { type: 'enrichment', label: 'Enrichment' },
      { type: 'risk_calculation', label: 'Risk Calculation' }
    ];
    
    const legendItems = legend.selectAll(".legend-item")
      .data(legendData)
      .enter()
      .append("g")
      .attr("class", "legend-item")
      .attr("transform", (d, i) => `translate(0, ${i * 25})`);
    
    legendItems.append("circle")
      .attr("r", 6)
      .attr("class", d => `legend-circle ${d.type}`);
    
    legendItems.append("text")
      .attr("x", 15)
      .attr("y", 4)
      .text(d => d.label);
    
    // Add title to the graph
    svg.append("text")
      .attr("class", "graph-title")
      .attr("x", width / 2)
      .attr("y", 30)
      .attr("text-anchor", "middle")
      .text(`${riskType.charAt(0).toUpperCase() + riskType.slice(1)} Risk Data Lineage`);
    
    // Add reporting date as subtitle
    if (graphData.reportingDate) {
      svg.append("text")
        .attr("class", "graph-subtitle")
        .attr("x", width / 2)
        .attr("y", 55)
        .attr("text-anchor", "middle")
        .text(`Reporting Date: ${graphData.reportingDate}`);
    }
    
    // Reset view to fit all nodes
    svg.call(zoom.transform, d3.zoomIdentity);
    
    console.log('Graph rendering complete');
  };
  
  // Helper functions for node visualization
  const getNodeSize = (type) => {
    switch (type) {
      case 'risk': return 30;
      case 'transaction': return 15;
      case 'validation': return 12;
      case 'enrichment': return 12;
      case 'risk_calculation': return 18;
      default: return 10;
    }
  };
  
  const getNodeIcon = (type) => {
    switch (type) {
      case 'risk': return '📊';
      case 'transaction': return '💱';
      case 'validation': return '✓';
      case 'enrichment': return '✚';
      case 'risk_calculation': return '🧮';
      default: return '●';
    }
  };
  
  // Render controls panel with helpful information
  const renderControls = () => {
    return (
      <div className="graph-controls">
        <div className="controls-header">
          <h3>Controls</h3>
        </div>
        <div className="controls-content">
          <p>
            <strong>Drag:</strong> Move nodes around
          </p>
          <p>
            <strong>Click:</strong> Select a node to view details
          </p>
          <p>
            <strong>Scroll:</strong> Zoom in/out
          </p>
          <p>
            <strong>Double Click:</strong> Reset view
          </p>
        </div>
        <div className="reset-view-btn" onClick={() => {
          d3.select(svgRef.current)
            .transition()
            .duration(750)
            .call(d3.zoom().transform, d3.zoomIdentity);
        }}>
          <i className="fas fa-home"></i> Reset View
        </div>
      </div>
    );
  };
  
  // Main render - graph visualization
  return (
    <div className="risk-lineage-graph-container" ref={containerRef}>
      <svg ref={svgRef} className="graph-svg"></svg>
      
      {renderControls()}
      
      {/* Node details panel */}
      {selectedNode && (
        <div className="node-details-panel">
          <div className="details-header">
            <h3>{selectedNode.label || selectedNode.id}</h3>
            <button className="close-details-btn" onClick={() => setSelectedNode(null)}>
              <i className="fas fa-times"></i>
            </button>
          </div>
          
          <div className="details-content">
            <p className="detail-type">
              <strong>Type:</strong>
              <span className={`type-badge ${selectedNode.type}`}>
                {selectedNode.type.charAt(0).toUpperCase() + selectedNode.type.slice(1).replace('_', ' ')}
              </span>
            </p>
            
            {selectedNode.type === 'risk' && (
              <>
                <p className="detail-item">
                  <strong>Aggregated Value:</strong>
                  <span>${(graphData?.aggregatedValue / 1000000).toFixed(2)}M</span>
                </p>
                <p className="detail-item">
                  <strong>Reporting Date:</strong>
                  <span>{graphData?.reportingDate}</span>
                </p>
              </>
            )}
            
            {selectedNode.type === 'transaction' && selectedNode.details && (
              <>
                <p className="detail-item">
                  <strong>Asset Class:</strong>
                  <span>{selectedNode.details.asset_class}</span>
                </p>
                <p className="detail-item">
                  <strong>Counterparty:</strong>
                  <span>{selectedNode.details.counterparty}</span>
                </p>
                <p className="detail-item">
                  <strong>Notional Amount:</strong>
                  <span>${selectedNode.details.notional_amount.toLocaleString()}</span>
                </p>
                <p className="detail-item">
                  <strong>Execution Date:</strong>
                  <span>{new Date(selectedNode.details.execution_timestamp).toLocaleDateString()}</span>
                </p>
              </>
            )}
            
            {selectedNode.type === 'validation' && selectedNode.details && (
              <>
                <p className="detail-item">
                  <strong>Validation Status:</strong>
                  <span>{selectedNode.details.validation_status}</span>
                </p>
              </>
            )}
            
            {selectedNode.type === 'enrichment' && selectedNode.details && (
              <>
                <p className="detail-item">
                  <strong>Market Data Source:</strong>
                  <span>{selectedNode.details.market_data_source}</span>
                </p>
                <p className="detail-item">
                  <strong>Sector:</strong>
                  <span>{selectedNode.details.sector}</span>
                </p>
              </>
            )}
            
            {selectedNode.type === 'risk_calculation' && selectedNode.details && (
              <>
                <p className="detail-item">
                  <strong>Method:</strong>
                  <span>{selectedNode.details.method || 'Standard'}</span>
                </p>
                <p className="detail-item highlight">
                  <strong>{riskType.charAt(0).toUpperCase() + riskType.slice(1)} Risk:</strong>
                  <span>${selectedNode.details[`${riskType}_risk_exposure`].toLocaleString()}</span>
                </p>
              </>
            )}
          </div>
        </div>
      )}
      
      {/* Add a message for empty data */}
      {(!graphData || (graphData.nodes && graphData.nodes.length === 0)) && (
        <div className="no-data-message">
          <p>No data available for {riskType} risk. Please try a different risk type.</p>
        </div>
      )}
    </div>
  );
};

export default RiskDataLineageGraph; 