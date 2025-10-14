import React from 'react';
import { Users, Package, MapPin } from 'lucide-react';

const WorldStatePanel = ({ world }) => {
  const characters = world?.characters || {};
  const items = world?.items || {};
  const locations = world?.locations || {};

  const hasData = Object.keys(characters).length > 0 || 
                  Object.keys(items).length > 0 || 
                  Object.keys(locations).length > 0;

  if (!hasData) {
    return (
      <div className="world-panel">
        <h3>🌍 World State</h3>
        <div className="empty-state">
          <p>No world data yet. Start playing to see characters, items, and locations!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="world-panel">
      <h3>🌍 World State</h3>
      
      {Object.keys(characters).length > 0 && (
        <div className="world-section">
          <h4>
            <Users size={16} />
            Characters
          </h4>
          <div className="world-items">
            {Object.entries(characters).map(([name, char]) => (
              <div key={name} className="world-item">
                <strong>{name}</strong>
                {char.location && (
                  <div>📍 {char.location}</div>
                )}
                {char.items && char.items.length > 0 && (
                  <div>🎒 {char.items.join(', ')}</div>
                )}
                {char.description && (
                  <div className="description">{char.description}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {Object.keys(items).length > 0 && (
        <div className="world-section">
          <h4>
            <Package size={16} />
            Items
          </h4>
          <div className="world-items">
            {Object.entries(items).map(([name, item]) => (
              <div key={name} className="world-item">
                <strong>{name}</strong>
                {item.owner && (
                  <div>👤 {item.owner}</div>
                )}
                {item.location && (
                  <div>📍 {item.location}</div>
                )}
                {item.description && (
                  <div className="description">{item.description}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {Object.keys(locations).length > 0 && (
        <div className="world-section">
          <h4>
            <MapPin size={16} />
            Locations
          </h4>
          <div className="world-items">
            {Object.entries(locations).map(([name, location]) => (
              <div key={name} className="world-item">
                <strong>{name}</strong>
                {location.occupants && location.occupants.length > 0 && (
                  <div>👥 {location.occupants.join(', ')}</div>
                )}
                {location.items && location.items.length > 0 && (
                  <div>🎒 {location.items.join(', ')}</div>
                )}
                {location.description && (
                  <div className="description">{location.description}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default WorldStatePanel;

