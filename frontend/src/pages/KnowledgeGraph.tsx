import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';
import { Card, Badge } from '../components/ui';
import { fetchKnowledgeGraph, type KnowledgeGraphDTO } from '../hooks/useApi';

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  strength: number;
  size: number;
  category: string;
}

interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  strength: number;
}

const categoryColors: Record<string, string> = {
  specialty: '#2D5C3F',
  diagnosis: '#4A7C8C',
  symptom: '#C85835',
  investigation: '#D4803F',
};

const categoryLabels: Record<string, string> = {
  specialty: 'Specialty',
  diagnosis: 'Diagnosis',
  symptom: 'Symptom',
  investigation: 'Investigation',
};

export const KnowledgeGraphPage: React.FC = () => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [dimensions, setDimensions] = useState({ width: 900, height: 600 });
  const [graphData, setGraphData] = useState<KnowledgeGraphDTO | null>(null);

  useEffect(() => {
    fetchKnowledgeGraph().then(setGraphData).catch(() => {});
  }, []);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width, height: Math.max(500, rect.width * 0.6) });
      }
    };
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  useEffect(() => {
    if (!svgRef.current || !graphData) return;

    const { width, height } = dimensions;

    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    // Deep copy data for D3 mutation
    const nodes: GraphNode[] = graphData.nodes.map(d => ({ ...d }));
    const links: GraphLink[] = graphData.links.map(d => ({ ...d }));

    const simulation = d3.forceSimulation<GraphNode>(nodes)
      .force('link', d3.forceLink<GraphNode, any>(links).id((d: any) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius((d: any) => 10 + d.size * 1.5));

    // Draw links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', (d: any) => d.strength > 0.6 ? '#2D5C3F' : d.strength > 0.4 ? '#D4803F' : '#C85835')
      .attr('stroke-width', (d: any) => Math.max(1, d.strength * 4))
      .attr('stroke-opacity', 0.5);

    // Draw nodes
    const node = svg.append('g')
      .selectAll('circle')
      .data(nodes)
      .enter()
      .append('circle')
      .attr('r', (d) => 8 + d.size * 1.5)
      .attr('fill', (d) => {
        const baseColor = categoryColors[d.category] || '#2D5C3F';
        return d.strength > 0.6 ? baseColor : baseColor + '80';
      })
      .attr('stroke', '#FFFCF7')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('click', (_event: any, d: GraphNode) => {
        setSelectedNode(d);
      })
      .call(d3.drag<any, GraphNode>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      );

    // Labels
    const label = svg.append('g')
      .selectAll('text')
      .data(nodes)
      .enter()
      .append('text')
      .text((d) => d.id)
      .attr('font-size', (d) => d.size > 8 ? '12px' : '10px')
      .attr('font-weight', (d) => d.size > 8 ? '600' : '400')
      .attr('fill', '#2A2520')
      .attr('text-anchor', 'middle')
      .attr('dy', (d) => -(12 + d.size * 1.5))
      .style('pointer-events', 'none');

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node
        .attr('cx', (d) => Math.max(20, Math.min(width - 20, d.x || 0)))
        .attr('cy', (d) => Math.max(20, Math.min(height - 20, d.y || 0)));

      label
        .attr('x', (d) => Math.max(20, Math.min(width - 20, d.x || 0)))
        .attr('y', (d) => Math.max(20, Math.min(height - 20, d.y || 0)));
    });

    return () => {
      simulation.stop();
    };
  }, [dimensions, graphData]);

  const weakLinks = (graphData?.links || [])
    .filter((l) => l.strength < 0.5)
    .sort((a, b) => a.strength - b.strength)
    .slice(0, 5);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      <div>
        <h1 className="text-2xl md:text-[2.25rem] font-bold text-text-primary mb-3">
          Your Knowledge Map
        </h1>
        <p className="text-lg text-text-secondary">
          Interactive visualization of your medical knowledge connections. Stronger connections mean better pattern recognition.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Graph */}
        <div className="lg:col-span-3">
          <Card padding="md">
            <div ref={containerRef} className="w-full">
              {graphData ? (
                <svg ref={svgRef} className="w-full" />
              ) : (
                <div className="h-[500px] flex items-center justify-center text-text-tertiary">Loading knowledge graph...</div>
              )}
            </div>
            {/* Legend */}
            <div className="flex flex-wrap gap-6 mt-4 pt-4 border-t border-warm-gray-100">
              {Object.entries(categoryLabels).map(([key, label]) => (
                <div key={key} className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: categoryColors[key] }}
                  />
                  <span className="text-sm text-text-secondary">{label}</span>
                </div>
              ))}
              <div className="flex items-center gap-2 ml-4">
                <div className="w-8 h-0.5 bg-forest-green" />
                <span className="text-sm text-text-secondary">Strong</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-8 h-0.5 bg-terracotta" />
                <span className="text-sm text-text-secondary">Weak</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          {/* Selected Node Info */}
          {selectedNode ? (
            <Card padding="md">
              <h3 className="text-base font-semibold text-text-primary mb-3">{selectedNode.id}</h3>
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-text-tertiary">Category</span>
                  <div className="mt-1">
                    <Badge variant={selectedNode.strength > 0.6 ? 'success' : 'warning'}>
                      {categoryLabels[selectedNode.category] || selectedNode.category}
                    </Badge>
                  </div>
                </div>
                <div>
                  <span className="text-sm text-text-tertiary">Mastery Level</span>
                  <div className="mt-1 flex items-center gap-2">
                    <div className="flex-1 bg-warm-gray-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${selectedNode.strength * 100}%`,
                          backgroundColor: selectedNode.strength > 0.7 ? '#2D5C3F' : selectedNode.strength > 0.5 ? '#D4803F' : '#C85835',
                        }}
                      />
                    </div>
                    <span className="text-sm font-semibold">{Math.round(selectedNode.strength * 100)}%</span>
                  </div>
                </div>
                <div>
                  <span className="text-sm text-text-tertiary">Cases Encountered</span>
                  <p className="text-base font-semibold text-text-primary">{selectedNode.size}</p>
                </div>
              </div>
            </Card>
          ) : (
            <Card padding="md" className="text-center">
              <p className="text-sm text-text-tertiary">Click a node to see details</p>
            </Card>
          )}

          {/* Weak Areas */}
          <Card padding="md">
            <h3 className="text-base font-semibold text-text-primary mb-4">Weak Connections</h3>
            <div className="space-y-3">
              {weakLinks.map((link, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="text-text-secondary">
                    {String(link.source)} → {String(link.target)}
                  </span>
                  <Badge variant="error" size="sm">
                    {Math.round(link.strength * 100)}%
                  </Badge>
                </div>
              ))}
              {weakLinks.length === 0 && (
                <p className="text-sm text-text-tertiary">No weak connections found</p>
              )}
            </div>
          </Card>

          {/* Summary Stats */}
          {graphData && (
            <Card padding="md">
              <h3 className="text-base font-semibold text-text-primary mb-4">Graph Summary</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-text-secondary">Total Concepts</span>
                  <span className="font-semibold">{graphData.nodes.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Connections</span>
                  <span className="font-semibold">{graphData.links.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Avg. Mastery</span>
                  <span className="font-semibold">
                    {Math.round(graphData.nodes.reduce((a, n) => a + n.strength, 0) / graphData.nodes.length * 100)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">Weak Links</span>
                  <span className="font-semibold text-terracotta">
                    {graphData.links.filter(l => l.strength < 0.5).length}
                  </span>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
