import React from 'react';

interface Trade {
  id: number;
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  commission: number;
  realized_pnl: number;
  status: string;
  executed_at: string | null;
  created_at: string;
}

interface TradesPanelProps {
  trades: Trade[];
  loading: boolean;
}

const TradesPanel: React.FC<TradesPanelProps> = ({ trades, loading }) => {
  if (loading) {
    return (
      <div className="trades-panel">
        <h2>📋 Recent Trades</h2>
        <div className="loading-spinner">Loading trades...</div>
      </div>
    );
  }

  if (trades.length === 0) {
    return (
      <div className="trades-panel">
        <h2>📋 Recent Trades</h2>
        <div className="empty-state">
          <p>No trades yet</p>
          <small>Trade history will appear here after executing orders</small>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'filled': return 'success';
      case 'pending': return 'warning';
      case 'cancelled': return 'danger';
      case 'rejected': return 'danger';
      default: return 'secondary';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'filled': return '✅';
      case 'pending': return '⏳';
      case 'cancelled': return '❌';
      case 'rejected': return '🚫';
      default: return '❓';
    }
  };

  return (
    <div className="trades-panel">
      <h2>📋 Recent Trades</h2>
      
      <div className="trades-list">
        {trades.slice(0, 10).map((trade) => (
          <div key={trade.id} className="trade-card">
            <div className="trade-header">
              <div className="trade-info">
                <h4>{trade.symbol}</h4>
                <span className={`trade-side ${trade.side.toLowerCase()}`}>
                  {trade.side.toUpperCase()}
                </span>
              </div>
              <div className="trade-status">
                <span className={`status-badge ${getStatusColor(trade.status)}`}>
                  {getStatusIcon(trade.status)} {trade.status}
                </span>
              </div>
            </div>
            
            <div className="trade-details">
              <div className="detail-row">
                <div className="detail-item">
                  <span className="label">Quantity:</span>
                  <span className="value">{trade.quantity}</span>
                </div>
                <div className="detail-item">
                  <span className="label">Price:</span>
                  <span className="value">
                    {trade.price > 0 ? `$${trade.price.toFixed(2)}` : 'Market'}
                  </span>
                </div>
              </div>
              
              <div className="detail-row">
                <div className="detail-item">
                  <span className="label">Total Value:</span>
                  <span className="value">
                    ${(trade.quantity * trade.price).toFixed(2)}
                  </span>
                </div>
                {trade.realized_pnl !== 0 && (
                  <div className="detail-item">
                    <span className="label">P&L:</span>
                    <span className={`value ${trade.realized_pnl >= 0 ? 'positive' : 'negative'}`}>
                      ${trade.realized_pnl.toFixed(2)}
                    </span>
                  </div>
                )}
              </div>
              
              <div className="trade-timestamp">
                <small>
                  {trade.status === 'filled' && trade.executed_at
                    ? `Executed: ${new Date(trade.executed_at).toLocaleString()}`
                    : `Created: ${new Date(trade.created_at).toLocaleString()}`
                  }
                </small>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {trades.length > 10 && (
        <div className="trades-footer">
          <small>Showing latest 10 of {trades.length} trades</small>
        </div>
      )}
    </div>
  );
};

export default TradesPanel;