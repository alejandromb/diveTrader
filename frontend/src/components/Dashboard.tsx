import React, { useState, useEffect } from 'react';
import axios from 'axios';
import StrategyCard from './StrategyCard';
import PerformanceChart from './PerformanceChart';
import BacktestModal from './BacktestModal';
import './Dashboard.css';

interface Strategy {
  id: number;
  name: string;
  strategy_type: string;
  is_active: boolean;
  initial_capital: number;
  current_capital: number;
  created_at: string;
}

interface Performance {
  strategy_id: number;
  roi_percentage: number;
  total_trades: number;
  win_rate: number;
  total_pnl: number;
  sharpe_ratio: number | null;
  max_drawdown: number | null;
}

const API_BASE = 'http://localhost:8000/api';

const Dashboard: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<number | null>(null);
  const [performance, setPerformance] = useState<Performance | null>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showBacktest, setShowBacktest] = useState(false);

  useEffect(() => {
    fetchStrategies();
  }, []);

  useEffect(() => {
    if (selectedStrategy) {
      fetchPerformance(selectedStrategy);
      fetchChartData(selectedStrategy);
    }
  }, [selectedStrategy]);

  const fetchStrategies = async () => {
    try {
      const response = await axios.get(`${API_BASE}/strategies/`);
      setStrategies(response.data);
      if (response.data.length > 0 && !selectedStrategy) {
        setSelectedStrategy(response.data[0].id);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching strategies:', error);
      setLoading(false);
    }
  };

  const fetchPerformance = async (strategyId: number) => {
    try {
      const response = await axios.get(`${API_BASE}/strategies/${strategyId}/performance`);
      setPerformance(response.data);
    } catch (error) {
      console.error('Error fetching performance:', error);
    }
  };

  const fetchChartData = async (strategyId: number) => {
    try {
      const response = await axios.get(`${API_BASE}/strategies/${strategyId}/daily-metrics?days=30`);
      setChartData(response.data);
    } catch (error) {
      console.error('Error fetching chart data:', error);
    }
  };

  const startStrategy = async (strategyId: number) => {
    try {
      await axios.post(`${API_BASE}/strategies/${strategyId}/start`);
      fetchStrategies(); // Refresh strategies
    } catch (error) {
      console.error('Error starting strategy:', error);
    }
  };

  const stopStrategy = async (strategyId: number) => {
    try {
      await axios.post(`${API_BASE}/strategies/${strategyId}/stop`);
      fetchStrategies(); // Refresh strategies
    } catch (error) {
      console.error('Error stopping strategy:', error);
    }
  };

  const createStrategy = async () => {
    try {
      const newStrategy = {
        name: `BTC Strategy ${strategies.length + 1}`,
        strategy_type: 'btc_scalping',
        initial_capital: 10000.0
      };
      const response = await axios.post(`${API_BASE}/strategies/`, newStrategy);
      setStrategies([...strategies, response.data]);
    } catch (error) {
      console.error('Error creating strategy:', error);
    }
  };

  if (loading) {
    return <div className="loading">Loading DiveTrader...</div>;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🏊‍♂️ DiveTrader</h1>
        <p>Automated Trading Platform</p>
      </header>

      <div className="dashboard-controls">
        <button onClick={createStrategy} className="btn btn-primary">
          + Create Strategy
        </button>
        <button 
          onClick={() => setShowBacktest(true)} 
          className="btn btn-secondary"
          disabled={!selectedStrategy}
        >
          📊 Backtest
        </button>
      </div>

      <div className="dashboard-content">
        <div className="strategies-panel">
          <h2>Trading Strategies</h2>
          {strategies.length === 0 ? (
            <div className="empty-state">
              <p>No strategies yet. Create your first strategy!</p>
            </div>
          ) : (
            strategies.map(strategy => (
              <StrategyCard
                key={strategy.id}
                strategy={strategy}
                isSelected={selectedStrategy === strategy.id}
                onSelect={() => setSelectedStrategy(strategy.id)}
                onStart={() => startStrategy(strategy.id)}
                onStop={() => stopStrategy(strategy.id)}
              />
            ))
          )}
        </div>

        <div className="performance-panel">
          {selectedStrategy && performance ? (
            <>
              <h2>Performance Metrics</h2>
              <div className="metrics-grid">
                <div className="metric-card">
                  <h3>ROI</h3>
                  <p className={performance.roi_percentage >= 0 ? 'positive' : 'negative'}>
                    {performance.roi_percentage.toFixed(2)}%
                  </p>
                </div>
                <div className="metric-card">
                  <h3>Total P&L</h3>
                  <p className={performance.total_pnl >= 0 ? 'positive' : 'negative'}>
                    ${performance.total_pnl.toFixed(2)}
                  </p>
                </div>
                <div className="metric-card">
                  <h3>Win Rate</h3>
                  <p>{performance.win_rate.toFixed(1)}%</p>
                </div>
                <div className="metric-card">
                  <h3>Total Trades</h3>
                  <p>{performance.total_trades}</p>
                </div>
                <div className="metric-card">
                  <h3>Sharpe Ratio</h3>
                  <p>{performance.sharpe_ratio?.toFixed(3) || 'N/A'}</p>
                </div>
                <div className="metric-card">
                  <h3>Max Drawdown</h3>
                  <p>{performance.max_drawdown?.toFixed(2) || 'N/A'}%</p>
                </div>
              </div>

              <div className="chart-container">
                <h3>Performance Chart</h3>
                <PerformanceChart data={chartData} />
              </div>
            </>
          ) : (
            <div className="empty-performance">
              <p>Select a strategy to view performance</p>
            </div>
          )}
        </div>
      </div>

      {showBacktest && selectedStrategy && (
        <BacktestModal
          strategyId={selectedStrategy}
          onClose={() => setShowBacktest(false)}
        />
      )}
    </div>
  );
};

export default Dashboard;