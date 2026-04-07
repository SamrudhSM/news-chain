import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

export default function GraphVisualization({ graphData }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  
  // Tooltip State
  const [tooltip, setTooltip] = useState({ show: false, x: 0, y: 0, data: null });

  useEffect(() => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
      return;
    }

    const width = containerRef.current.clientWidth;
    const height = 600;

    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', [0, 0, width, height]);

    const g = svg.append('g');
    svg.call(d3.zoom().scaleExtent([0.1, 4]).on('zoom', (event) => {
      g.attr('transform', event.transform);
    }));

    // Clone data
    const nodes = graphData.nodes.map(d => ({ ...d }));
    const links = graphData.edges.map(d => ({ ...d, source: d.source, target: d.target }));

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(150))
      .force('charge', d3.forceManyBody().strength(-600))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide().radius(60));

    // Force marker definitions (arrows)
    svg.append("defs").selectAll("marker")
      .data(["end"]) 
      .join("marker")
        .attr("id", String)
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 25)
        .attr("refY", 0)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
      .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("fill", "#64748b");

    // Edges
    const linkGroup = g.append('g')
      .selectAll('g')
      .data(links)
      .join('g');

    const linkPaths = linkGroup.append('line')
      .attr('class', 'link')
      .attr('stroke', '#64748b')
      .attr('stroke-width', 2)
      .attr('marker-end', 'url(#end)');

    const linkLabels = linkGroup.append('text')
      .attr('font-size', '10px')
      .attr('font-family', 'JetBrains Mono, monospace')
      .attr('fill', '#94a3b8')
      .attr('text-anchor', 'middle')
      .attr('dy', -5)
      .text(d => d.type);

    // Nodes
    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node')
      .call(drag(simulation))
      .on('mouseover', (event, d) => {
        setTooltip({ show: true, x: event.pageX + 10, y: event.pageY + 10, data: d });
        d3.select(event.currentTarget).select('circle').attr('stroke', '#fff').attr('stroke-width', 4);
      })
      .on('mousemove', (event) => {
        setTooltip(prev => ({ ...prev, x: event.pageX + 10, y: event.pageY + 10 }));
      })
      .on('mouseout', (event) => {
        setTooltip({ show: false, x: 0, y: 0, data: null });
        d3.select(event.currentTarget).select('circle').attr('stroke', 'var(--border-light)').attr('stroke-width', 2);
      });

    // Colors: Red=Event, Blue=Entity, Green=Topic
    const getRadius = (labels) => labels.includes('Event') ? 18 : 12;
    const getColor = (labels) => {
      if (labels.includes('Event')) return 'var(--risk-high)';
      if (labels.includes('Entity')) return 'var(--ent-country)';
      if (labels.includes('Topic')) return 'var(--risk-low)';
      return '#64748b';
    };

    node.append('circle')
      .attr('r', d => getRadius(d.labels))
      .attr('fill', d => getColor(d.labels));

    node.append('text')
      .attr('x', 24)
      .attr('y', 4)
      .text(d => d.properties?.name || d.properties?.title || 'Unknown')
      .attr('fill', '#f8fafc');

    simulation.on('tick', () => {
      linkPaths
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      linkLabels
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    return () => { simulation.stop(); };
  }, [graphData]);

  const drag = (simulation) => {
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x; d.fy = d.y;
    }
    function dragged(event, d) {
      d.fx = event.x; d.fy = event.y;
    }
    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null; d.fy = null;
    }
    return d3.drag().on('start', dragstarted).on('drag', dragged).on('end', dragended);
  };

  return (
    <div className="glass-panel graph-container animate-in" ref={containerRef}>
      
      {/* Absolute Legend */}
      <div className="graph-legend">
        <div className="legend-item">
          <div className="legend-dot" style={{ background: 'var(--risk-high)' }}></div>
          <span>Event</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ background: 'var(--ent-country)' }}></div>
          <span>Entity</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ background: 'var(--risk-low)' }}></div>
          <span>Topic</span>
        </div>
      </div>

      {/* SVG Canvas */}
      {!graphData || !graphData.nodes || graphData.nodes.length === 0 ? (
        <div className="loader-wrapper" style={{ height: '100%' }}>
          <span className="mono" style={{ color: 'var(--text-muted)' }}>NO GRAPH DATA DETECTED</span>
        </div>
      ) : (
        <svg ref={svgRef}></svg>
      )}

      {/* Tooltip HTML */}
      {tooltip.show && tooltip.data && (
        <div className="d3-tooltip" style={{ left: tooltip.x, top: tooltip.y }}>
          <div className="tt-title">{tooltip.data.properties.name || tooltip.data.properties.title}</div>
          <div className="tt-row">
            <span className="tt-label">Type</span>
            <span>{tooltip.data.labels?.join(', ')}</span>
          </div>
          {tooltip.data.properties.risk_score !== undefined && (
            <div className="tt-row">
              <span className="tt-label">Risk</span>
              <span style={{ color: 'var(--risk-high)', fontWeight: 'bold' }}>{tooltip.data.properties.risk_score}</span>
            </div>
          )}
          {tooltip.data.properties.type && (
            <div className="tt-row">
              <span className="tt-label">Subtype</span>
              <span>{tooltip.data.properties.type}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
