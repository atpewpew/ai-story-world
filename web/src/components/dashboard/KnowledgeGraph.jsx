import { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';
import { Maximize2, Minimize2 } from 'lucide-react';

export default function KnowledgeGraph({ sessionId, world }) {
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  const [expanded, setExpanded] = useState(false);
  
  useEffect(() => {
    if (!containerRef.current || !world) return;
    
    const nodes = [];
    const edges = [];
    let nodeId = 0;
    const nodeMap = new Map(); // To avoid duplicate nodes
    
    // Add character nodes
    Object.entries(world.characters || {}).forEach(([name, char]) => {
      if (!nodeMap.has(name)) {
        const id = nodeId++;
        nodeMap.set(name, id);
        nodes.push({
          id,
          label: name,
          group: 'character',
          shape: 'dot',
          size: 20,
          color: '#7c5cff'
        });
      }
      
      // Add ownership edges
      if (char.items && Array.isArray(char.items)) {
        char.items.forEach(item => {
          let itemId;
          if (nodeMap.has(item)) {
            itemId = nodeMap.get(item);
          } else {
            itemId = nodeId++;
            nodeMap.set(item, itemId);
            nodes.push({
              id: itemId,
              label: item,
              group: 'item',
              shape: 'box',
              color: '#ffb86b'
            });
          }
          edges.push({
            from: nodeMap.get(name),
            to: itemId,
            label: 'OWNS',
            arrows: 'to',
            color: '#4dd4e8'
          });
        });
      }
      
      // Add location edges
      if (char.location) {
        let locationId;
        if (nodeMap.has(char.location)) {
          locationId = nodeMap.get(char.location);
        } else {
          locationId = nodeId++;
          nodeMap.set(char.location, locationId);
          nodes.push({
            id: locationId,
            label: char.location,
            group: 'location',
            shape: 'diamond',
            color: '#10b981'
          });
        }
        edges.push({
          from: nodeMap.get(name),
          to: locationId,
          label: 'AT',
          arrows: 'to',
          color: '#f59e0b'
        });
      }
    });
    
    // Add item nodes that aren't owned
    Object.entries(world.items || {}).forEach(([name, item]) => {
      if (!nodeMap.has(name)) {
        const id = nodeId++;
        nodeMap.set(name, id);
        nodes.push({
          id,
          label: name,
          group: 'item',
          shape: 'box',
          color: '#ffb86b'
        });
      }
    });
    
    // Add location nodes
    Object.entries(world.locations || {}).forEach(([name, location]) => {
      if (!nodeMap.has(name)) {
        const id = nodeId++;
        nodeMap.set(name, id);
        nodes.push({
          id,
          label: name,
          group: 'location',
          shape: 'diamond',
          color: '#10b981'
        });
      }
    });
    
    const data = { nodes, edges };
    const options = {
      physics: {
        stabilization: false,
        barnesHut: {
          gravitationalConstant: -2000,
          springConstant: 0.001,
          springLength: 200
        }
      },
      interaction: {
        hover: true,
        zoomView: true,
        dragView: true
      },
      groups: {
        character: {
          color: { background: '#7c5cff', border: '#5a3fd8' },
          font: { color: 'white' }
        },
        item: {
          color: { background: '#ffb86b', border: '#f59e0b' },
          font: { color: 'white' }
        },
        location: {
          color: { background: '#10b981', border: '#059669' },
          font: { color: 'white' }
        }
      }
    };
    
    if (networkRef.current) {
      networkRef.current.destroy();
    }
    
    networkRef.current = new Network(containerRef.current, data, options);
    
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
      }
    };
  }, [world]);
  
  if (!world || (Object.keys(world.characters || {}).length === 0 && 
                 Object.keys(world.items || {}).length === 0 && 
                 Object.keys(world.locations || {}).length === 0)) {
    return (
      <div className="knowledge-graph">
        <div className="kg-header">
          <h4>Knowledge Graph</h4>
        </div>
        <div className="empty-state">
          <p>No world data yet. Start playing to see the knowledge graph!</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className={`knowledge-graph ${expanded ? 'expanded' : ''}`}>
      <div className="kg-header">
        <h4>Knowledge Graph</h4>
        <button onClick={() => setExpanded(!expanded)}>
          {expanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
        </button>
      </div>
      <div ref={containerRef} className="kg-container" />
    </div>
  );
}
