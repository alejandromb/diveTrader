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

interface TradeAnalyticsProps {
  trades: Trade[];
  currentCapital: number;
  initialCapital: number;
}

const TradeAnalytics: React.FC<TradeAnalyticsProps> = ({ 
  trades, 
  currentCapital, 
  initialCapital 
}) => {
  if (trades.length === 0) {
    return (
      <div className="trade-analytics">
        <h3>📊 Trade Analytics</h3>
        <div className="empty-analytics">
          <p>No trade data available</p>
          <small>Analytics will appear after executing trades</small>
        </div>
      </div>
    );
  }

  // Calculate analytics
  const completedTrades = trades.filter(t => t.status === 'filled');
  const totalTrades = completedTrades.length;
  const winningTrades = completedTrades.filter(t => t.realized_pnl > 0);
  const losingTrades = completedTrades.filter(t => t.realized_pnl < 0);
  
  const winRate = totalTrades > 0 ? (winningTrades.length / totalTrades) * 100 : 0;
  // const totalPnL = completedTrades.reduce((sum, t) => sum + t.realized_pnl, 0);
  const totalVolume = completedTrades.reduce((sum, t) => sum + (t.quantity * t.price), 0);
  const avgTradeSize = totalTrades > 0 ? totalVolume / totalTrades : 0;
  
  const avgWin = winningTrades.length > 0 
    ? winningTrades.reduce((sum, t) => sum + t.realized_pnl, 0) / winningTrades.length 
    : 0;
  const avgLoss = losingTrades.length > 0 
    ? Math.abs(losingTrades.reduce((sum, t) => sum + t.realized_pnl, 0) / losingTrades.length)
    : 0;
  
  const profitFactor = avgLoss > 0 ? avgWin / avgLoss : 0;
  const totalReturn = initialCapital > 0 ? ((currentCapital - initialCapital) / initialCapital) * 100 : 0;
  
  // Recent activity (last 7 days)
  const recentTrades = completedTrades.filter(t => {
    const tradeDate = new Date(t.executed_at || t.created_at);
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    return tradeDate >= weekAgo;
  });

  // Symbol breakdown
  const symbolStats = completedTrades.reduce((acc, trade) => {
    if (!acc[trade.symbol]) {
      acc[trade.symbol] = { trades: 0, pnl: 0, volume: 0 };
    }
    acc[trade.symbol].trades += 1;
    acc[trade.symbol].pnl += trade.realized_pnl;
    acc[trade.symbol].volume += trade.quantity * trade.price;
    return acc;
  }, {} as Record<string, { trades: number; pnl: number; volume: number }>);

  return (
    <div className="trade-analytics">
      <h3>📊 Trade Analytics</h3>
      
      {/* Key Metrics */}
      <div className="analytics-section">
        <h4>Performance Summary</h4>
        <div className="metrics-row">
          <div className="analytics-metric">
            <span className="metric-label">Total Return</span>
            <span className={`metric-value ${totalReturn >= 0 ? 'positive' : 'negative'}`}>
              {totalReturn.toFixed(2)}%
            </span>
          </div>
          <div className="analytics-metric">
            <span className="metric-label">Win Rate</span>
            <span className="metric-value">{winRate.toFixed(1)}%</span>
          </div>
          <div className="analytics-metric">
            <span className="metric-label">Profit Factor</span>
            <span className="metric-value">{profitFactor.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Trade Statistics */}
      <div className="analytics-section">
        <h4>Trade Statistics</h4>
        <div className="stats-grid">
          <div className="stat-item">
            <span className="stat-label">Total Trades</span>
            <span className="stat-value">{totalTrades}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Winning Trades</span>
            <span className="stat-value positive">{winningTrades.length}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Losing Trades</span>
            <span className="stat-value negative">{losingTrades.length}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Avg Trade Size</span>
            <span className="stat-value">${avgTradeSize.toFixed(2)}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Avg Win</span>
            <span className="stat-value positive">${avgWin.toFixed(2)}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Avg Loss</span>
            <span className="stat-value negative">${avgLoss.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="analytics-section">
        <h4>Recent Activity (7 days)</h4>
        <div className="recent-activity">
          <div className="activity-stat">
            <span className="activity-label">Recent Trades:</span>
            <span className="activity-value">{recentTrades.length}</span>
          </div>
          <div className="activity-stat">
            <span className="activity-label">Recent P&L:</span>
            <span className={`activity-value ${recentTrades.reduce((sum, t) => sum + t.realized_pnl, 0) >= 0 ? 'positive' : 'negative'}`}>
              ${recentTrades.reduce((sum, t) => sum + t.realized_pnl, 0).toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Symbol Breakdown */}
      {Object.keys(symbolStats).length > 0 && (
        <div className="analytics-section">
          <h4>Symbol Performance</h4>
          <div className="symbol-breakdown">
            {Object.entries(symbolStats).map(([symbol, stats]) => (
              <div key={symbol} className="symbol-stat">
                <div className="symbol-info">
                  <span className="symbol-name">{symbol}</span>
                  <span className="symbol-trades">{stats.trades} trades</span>
                </div>
                <div className="symbol-pnl">
                  <span className={`pnl-value ${stats.pnl >= 0 ? 'positive' : 'negative'}`}>
                    ${stats.pnl.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TradeAnalytics;