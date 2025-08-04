import React, { useState, useMemo } from 'react';

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

type TimeFilter = 'all' | '4hours' | 'today' | 'week' | 'month';

interface EnhancedTradesPanelProps {
  trades: Trade[];
  loading: boolean;
}

const EnhancedTradesPanel: React.FC<EnhancedTradesPanelProps> = ({ trades, loading }) => {
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('today');
  const [symbolFilter, setSymbolFilter] = useState<string>('all');

  // Get unique symbols for filter dropdown
  const uniqueSymbols = useMemo(() => {
    const symbols = Array.from(new Set(trades.map(t => t.symbol)));
    return symbols.sort();
  }, [trades]);

  // Filter trades based on time and symbol
  const filteredTrades = useMemo(() => {
    let filtered = [...trades];

    // Time filter
    const now = new Date();
    const cutoffTime = (() => {
      switch (timeFilter) {
        case '4hours':
          return new Date(now.getTime() - 4 * 60 * 60 * 1000);
        case 'today':
          const today = new Date();
          today.setHours(0, 0, 0, 0);
          return today;
        case 'week':
          return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        case 'month':
          return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        default:
          return new Date(0); // Show all
      }
    })();

    filtered = filtered.filter(trade => {
      const tradeTime = new Date(trade.executed_at || trade.created_at);
      return tradeTime >= cutoffTime;
    });

    // Symbol filter
    if (symbolFilter !== 'all') {
      filtered = filtered.filter(trade => trade.symbol === symbolFilter);
    }

    // Sort by most recent first
    return filtered.sort((a, b) => {
      const timeA = new Date(a.executed_at || a.created_at).getTime();
      const timeB = new Date(b.executed_at || b.created_at).getTime();
      return timeB - timeA;
    });
  }, [trades, timeFilter, symbolFilter]);

  if (loading) {
    return (
      <div className="enhanced-trades-panel">
        <h2>📋 Recent Trades</h2>
        <div className="loading-spinner">Loading trades...</div>
      </div>
    );
  }

  if (trades.length === 0) {
    return (
      <div className="enhanced-trades-panel">
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
    <div className="enhanced-trades-panel">
      <div className="trades-header">
        <h2>📋 Recent Trades</h2>
        <div className="trades-filters">
          <select 
            value={timeFilter} 
            onChange={(e) => setTimeFilter(e.target.value as TimeFilter)}
            className="filter-select"
          >
            <option value="4hours">Last 4 Hours</option>
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="all">All Time</option>
          </select>
          
          <select 
            value={symbolFilter} 
            onChange={(e) => setSymbolFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Symbols</option>
            {uniqueSymbols.map(symbol => (
              <option key={symbol} value={symbol}>{symbol}</option>
            ))}
          </select>
        </div>
      </div>

      {filteredTrades.length === 0 ? (
        <div className="empty-state">
          <p>No trades found for selected filters</p>
          <small>Try adjusting the time period or symbol filter</small>
        </div>
      ) : (
        <>
          <div className="trades-stats">
            <div className="stat-item">
              <span className="stat-label">Trades Found:</span>
              <span className="stat-value">{filteredTrades.length}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Total P&L:</span>
              <span className={`stat-value pnl-value ${filteredTrades.reduce((sum, t) => sum + t.realized_pnl, 0) >= 0 ? 'positive' : 'negative'}`}>
                ${filteredTrades.reduce((sum, t) => sum + t.realized_pnl, 0).toFixed(2)}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Filled:</span>
              <span className="stat-value">{filteredTrades.filter(t => t.status === 'filled').length}</span>
            </div>
          </div>
          
          <div className="trades-list">
            {filteredTrades.slice(0, 20).map((trade) => (
              <div key={trade.id} className="enhanced-trade-card">
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
                      {trade.status === 'filled' && trade.executed_at ? (
                        <>
                          <span className="timestamp-label">Executed:</span>
                          <span className="timestamp-value">{new Date(trade.executed_at).toLocaleString()}</span>
                          <span className="time-ago">({getTimeAgo(new Date(trade.executed_at))})</span>
                        </>
                      ) : (
                        <>
                          <span className="timestamp-label">Created:</span>
                          <span className="timestamp-value">{new Date(trade.created_at).toLocaleString()}</span>
                          <span className="time-ago">({getTimeAgo(new Date(trade.created_at))})</span>
                        </>
                      )}
                    </small>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {filteredTrades.length > 20 && (
            <div className="trades-footer">
              <small>Showing latest 20 of {filteredTrades.length} filtered trades</small>
            </div>
          )}
        </>
      )}
    </div>
  );
};

// Helper function to show time ago
function getTimeAgo(date: Date): string {
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diffInSeconds < 60) {
    return `${diffInSeconds}s ago`;
  } else if (diffInSeconds < 3600) {
    return `${Math.floor(diffInSeconds / 60)}m ago`;
  } else if (diffInSeconds < 86400) {
    return `${Math.floor(diffInSeconds / 3600)}h ago`;
  } else {
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  }
}

export default EnhancedTradesPanel;