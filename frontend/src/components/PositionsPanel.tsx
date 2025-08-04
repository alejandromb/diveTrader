import React from 'react';

interface Position {
  id: number;
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  side: string;
  opened_at: string;
}

interface PositionsPanelProps {
  positions: Position[];
  loading: boolean;
}

const PositionsPanel: React.FC<PositionsPanelProps> = ({ positions, loading }) => {
  if (loading) {
    return (
      <div className="positions-panel">
        <h2>📊 Current Positions</h2>
        <div className="loading-spinner">Loading positions...</div>
      </div>
    );
  }

  if (positions.length === 0) {
    return (
      <div className="positions-panel">
        <h2>📊 Current Positions</h2>
        <div className="empty-state">
          <p>No active positions</p>
          <small>Positions will appear here after placing trades</small>
        </div>
      </div>
    );
  }

  const totalValue = positions.reduce((sum, pos) => sum + pos.market_value, 0);
  const totalPnL = positions.reduce((sum, pos) => sum + pos.unrealized_pnl, 0);

  return (
    <div className="positions-panel">
      <div className="positions-header">
        <h2>📊 Current Positions</h2>
        <div className="positions-summary">
          <span className="total-value">Total: ${totalValue.toFixed(2)}</span>
          <span className={`total-pnl ${totalPnL >= 0 ? 'positive' : 'negative'}`}>
            P&L: ${totalPnL.toFixed(2)}
          </span>
        </div>
      </div>
      
      <div className="positions-list">
        {positions.map((position) => {
          const pnlPercentage = ((position.current_price - position.avg_price) / position.avg_price) * 100;
          
          return (
            <div key={position.id} className="position-card">
              <div className="position-header">
                <div className="symbol-info">
                  <h4>{position.symbol}</h4>
                  <span className={`position-side ${position.side}`}>{position.side}</span>
                </div>
                <div className="position-value">
                  <span className="market-value">${position.market_value.toFixed(2)}</span>
                  <span className={`unrealized-pnl ${position.unrealized_pnl >= 0 ? 'positive' : 'negative'}`}>
                    ${position.unrealized_pnl.toFixed(2)} ({pnlPercentage.toFixed(2)}%)
                  </span>
                </div>
              </div>
              
              <div className="position-details">
                <div className="detail-item">
                  <span className="label">Quantity:</span>
                  <span className="value">{Math.abs(position.quantity)}</span>
                </div>
                <div className="detail-item">
                  <span className="label">Avg Price:</span>
                  <span className="value">${position.avg_price.toFixed(2)}</span>
                </div>
                <div className="detail-item">
                  <span className="label">Current Price:</span>
                  <span className="value">${position.current_price.toFixed(2)}</span>
                </div>
                <div className="detail-item">
                  <span className="label">Opened:</span>
                  <span className="value">{new Date(position.opened_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PositionsPanel;