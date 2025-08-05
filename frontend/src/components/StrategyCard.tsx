import React, { useState, useEffect, useRef } from 'react';
import type { Strategy } from '../types/api';

interface StrategyCardProps {
  strategy: Strategy;
  isSelected: boolean;
  onSelect: () => void;
  onStart: () => void;
  onStop: () => void;
  onDelete: () => void;
  onViewLogs?: () => void;
  onViewSettings?: () => void;
}

const StrategyCard: React.FC<StrategyCardProps> = ({
  strategy,
  isSelected,
  onSelect,
  onStart,
  onStop,
  onDelete,
  onViewLogs,
  onViewSettings
}) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDropdown]);

  const getStrategyIcon = (type: string) => {
    switch (type) {
      case 'btc_scalping':
        return '₿';
      case 'portfolio_distributor':
        return '📊';
      default:
        return '🤖';
    }
  };

  const getStrategyStatus = (strategy: Strategy) => {
    if (!strategy.is_active) {
      return {
        text: '🔴 Disabled',
        color: '#757575',
        description: 'Strategy is disabled'
      };
    } else if (strategy.is_running) {
      return {
        text: '🟢 Running',
        color: '#4CAF50',
        description: 'Strategy is active and executing trades'
      };
    } else {
      return {
        text: '🟡 Enabled but Stopped',
        color: '#FF9800',
        description: 'Strategy is enabled but not executing trades'
      };
    }
  };

  return (
    <div 
      className={`strategy-card ${isSelected ? 'selected' : ''}`}
      onClick={onSelect}
    >
      <div className="strategy-header">
        <div className="strategy-icon">
          {getStrategyIcon(strategy.strategy_type)}
        </div>
        <div className="strategy-info">
          <h4>{strategy.name}</h4>
          <p className="strategy-type">
            {strategy.strategy_type.replace('_', ' ').toUpperCase()}
          </p>
        </div>
        <div 
          className="strategy-status"
          style={{ color: getStrategyStatus(strategy).color }}
          title={getStrategyStatus(strategy).description}
        >
          {getStrategyStatus(strategy).text}
        </div>
      </div>

      <div className="strategy-metrics">
        <div className="metric">
          <span className="label">💰 Cash Allocation:</span>
          <span className="value">${strategy.initial_capital.toLocaleString()}</span>
        </div>
        <div className="metric">
          <span className="label">📈 Strategy P&L:</span>
          <span className={`value ${strategy.current_capital >= strategy.initial_capital ? 'positive' : 'negative'}`}>
            ${(strategy.current_capital - strategy.initial_capital).toLocaleString()} 
            ({(((strategy.current_capital - strategy.initial_capital) / strategy.initial_capital) * 100).toFixed(1)}%)
          </span>
        </div>
        <div className="metric">
          <span className="label">📅 Created:</span>
          <span className="value">
            {new Date(strategy.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      <div className="strategy-actions">
        <div className="left-actions">
          {strategy.is_running ? (
            <button 
              className="btn btn-danger"
              onClick={(e) => {
                e.stopPropagation();
                onStop();
              }}
            >
              Stop Strategy
            </button>
          ) : (
            <button 
              className="btn btn-success"
              onClick={(e) => {
                e.stopPropagation();
                onStart();
              }}
              disabled={!strategy.is_active}
              title={!strategy.is_active ? "Strategy must be enabled first" : "Start executing trades"}
            >
              Start Strategy
            </button>
          )}
          
          {onViewLogs && (
            <button 
              className="btn btn-outline-info btn-sm"
              onClick={(e) => {
                e.stopPropagation();
                onViewLogs();
              }}
              title="View Event Logs"
            >
              📋
            </button>
          )}
        </div>
        
        <div className="right-actions" style={{ position: 'relative' }} ref={dropdownRef}>
          <button 
            className="btn btn-outline-secondary btn-sm"
            onClick={(e) => {
              e.stopPropagation();
              setShowDropdown(!showDropdown);
            }}
            title="More Actions"
            style={{ padding: '4px 8px' }}
          >
            ⋮
          </button>
          
          {showDropdown && (
            <div 
              className="dropdown-menu"
              style={{
                position: 'absolute',
                top: '100%',
                right: '0',
                backgroundColor: 'white',
                border: '1px solid #ddd',
                borderRadius: '4px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                zIndex: 1000,
                minWidth: '150px',
                padding: '4px 0'
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {onViewSettings && (
                <button
                  className="dropdown-item"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowDropdown(false);
                    onViewSettings();
                  }}
                  style={{
                    width: '100%',
                    padding: '8px 16px',
                    border: 'none',
                    background: 'none',
                    textAlign: 'left',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                  onMouseOver={(e) => e.target.style.backgroundColor = '#f5f5f5'}
                  onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
                >
                  ⚙️ Settings
                </button>
              )}
              
              <div style={{ height: '1px', backgroundColor: '#eee', margin: '4px 0' }} />
              
              <button
                className="dropdown-item"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDropdown(false);
                  if (window.confirm(`Are you sure you want to delete "${strategy.name}"?`)) {
                    onDelete();
                  }
                }}
                style={{
                  width: '100%',
                  padding: '8px 16px',
                  border: 'none',
                  background: 'none',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontSize: '14px',
                  color: '#dc3545'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#f5f5f5'}
                onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
              >
                🗑️ Delete
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StrategyCard;