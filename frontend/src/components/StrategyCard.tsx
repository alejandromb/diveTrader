import React from 'react';

interface Strategy {
  id: number;
  name: string;
  strategy_type: string;
  is_active: boolean;
  is_running?: boolean;
  initial_capital: number;
  current_capital: number;
  created_at: string;
}

interface StrategyCardProps {
  strategy: Strategy;
  isSelected: boolean;
  onSelect: () => void;
  onStart: () => void;
  onStop: () => void;
  onDelete: () => void;
  onViewLogs?: () => void;
}

const StrategyCard: React.FC<StrategyCardProps> = ({
  strategy,
  isSelected,
  onSelect,
  onStart,
  onStop,
  onDelete,
  onViewLogs
}) => {
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
          <span className="label">Initial Capital:</span>
          <span className="value">${strategy.initial_capital.toLocaleString()}</span>
        </div>
        <div className="metric">
          <span className="label">Current Capital:</span>
          <span className="value">${strategy.current_capital.toLocaleString()}</span>
        </div>
        <div className="metric">
          <span className="label">Created:</span>
          <span className="value">
            {new Date(strategy.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      <div className="strategy-actions">
        <div className="primary-actions">
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
        </div>
        
        <div className="secondary-actions">
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
          <button 
            className="btn btn-outline-danger btn-sm"
            onClick={(e) => {
              e.stopPropagation();
              if (window.confirm(`Are you sure you want to delete "${strategy.name}"?`)) {
                onDelete();
              }
            }}
            title="Delete Strategy"
          >
            🗑️
          </button>
        </div>
      </div>
    </div>
  );
};

export default StrategyCard;