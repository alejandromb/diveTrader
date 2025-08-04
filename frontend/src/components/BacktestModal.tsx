import React, { useState } from 'react';
import axios from 'axios';

interface BacktestResult {
  symbol: string;
  period: string;
  initial_capital: number;
  final_capital: number;
  total_return: number;
  total_return_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  max_drawdown: number;
  sharpe_ratio: number;
}

interface BacktestModalProps {
  strategyId: number;
  onClose: () => void;
}

const BacktestModal: React.FC<BacktestModalProps> = ({ strategyId, onClose }) => {
  const [daysBack, setDaysBack] = useState(30);
  const [initialCapital, setInitialCapital] = useState(10000);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runBacktest = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(`http://localhost:8000/api/strategies/${strategyId}/backtest`, {
        days_back: daysBack,
        initial_capital: initialCapital
      });
      
      setResults(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Backtest failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📊 Strategy Backtest</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {!results ? (
            <div className="backtest-form">
              <div className="form-group">
                <label>Days to Test:</label>
                <input
                  type="number"
                  value={daysBack}
                  onChange={(e) => setDaysBack(Number(e.target.value))}
                  min="1"
                  max="365"
                />
              </div>

              <div className="form-group">
                <label>Initial Capital:</label>
                <input
                  type="number"
                  value={initialCapital}
                  onChange={(e) => setInitialCapital(Number(e.target.value))}
                  min="100"
                  step="100"
                />
              </div>

              {error && (
                <div className="error-message">
                  {error}
                </div>
              )}

              <div className="form-actions">
                <button 
                  onClick={runBacktest} 
                  disabled={loading}
                  className="btn btn-primary"
                >
                  {loading ? 'Running...' : 'Run Backtest'}
                </button>
                <button onClick={onClose} className="btn btn-secondary">
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="backtest-results">
              <h3>Backtest Results</h3>
              
              <div className="results-summary">
                <div className="result-item">
                  <strong>Period:</strong> {results.period}
                </div>
                <div className="result-item">
                  <strong>Symbol:</strong> {results.symbol}
                </div>
              </div>

              <div className="results-grid">
                <div className="result-card">
                  <h4>Capital</h4>
                  <p>Initial: ${results.initial_capital.toLocaleString()}</p>
                  <p>Final: ${results.final_capital.toLocaleString()}</p>
                </div>

                <div className="result-card">
                  <h4>Returns</h4>
                  <p className={results.total_return >= 0 ? 'positive' : 'negative'}>
                    Total: ${results.total_return.toFixed(2)}
                  </p>
                  <p className={results.total_return_pct >= 0 ? 'positive' : 'negative'}>
                    ROI: {results.total_return_pct.toFixed(2)}%
                  </p>
                </div>

                <div className="result-card">
                  <h4>Trades</h4>
                  <p>Total: {results.total_trades}</p>
                  <p className="positive">Wins: {results.winning_trades}</p>
                  <p className="negative">Losses: {results.losing_trades}</p>
                </div>

                <div className="result-card">
                  <h4>Statistics</h4>
                  <p>Win Rate: {results.win_rate.toFixed(1)}%</p>
                  <p>Max Drawdown: {results.max_drawdown.toFixed(2)}%</p>
                  <p>Sharpe Ratio: {results.sharpe_ratio.toFixed(3)}</p>
                </div>
              </div>

              <div className="results-actions">
                <button onClick={() => setResults(null)} className="btn btn-secondary">
                  Run Another Test
                </button>
                <button onClick={onClose} className="btn btn-primary">
                  Close
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BacktestModal;