import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_CONFIG } from '../config/constants';
import { apiV2, strategyHelpers } from '../services/apiV2';
import type { Strategy, StrategyType } from '../types/api';
import StrategyCard from './StrategyCard';
import PerformanceChart from './PerformanceChart';
import BacktestModal from './BacktestModal';
import AccountInfo from './AccountInfo';
import PositionsPanel from './PositionsPanel';
import EnhancedTradesPanel from './EnhancedTradesPanel';
import PriceTicker from './PriceTicker';
import TradeAnalytics from './TradeAnalytics';
import CreateStrategyModal, { type CreateStrategyData } from './CreateStrategyModal';
import RiskManagementPanel from './RiskManagementPanel';
import StrategyEventLogsModal from './StrategyEventLogsModal';
import StrategySettingsModal from './StrategySettingsModal';
import TypedSettingsModal from './TypedSettingsModal';
import './Dashboard.css';
import './EnhancedStyles.css';

// Using Strategy type from ../types/api.ts

interface Performance {
  strategy_id: number;
  roi_percentage: number;
  total_trades: number;
  win_rate: number;
  total_pnl: number;
  sharpe_ratio: number | null;
  max_drawdown: number | null;
}

interface AccountData {
  equity: number;
  cash: number;
  buying_power: number;
  portfolio_value: number;
  day_trade_count: number;
}

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

// ✅ FIXED: Now using centralized config with proper Vite env vars
const API_BASE = API_CONFIG.BASE_URL;

const Dashboard: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<number | null>(null);
  const [performance, setPerformance] = useState<Performance | null>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [accountData, setAccountData] = useState<AccountData | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [showBacktest, setShowBacktest] = useState(false);
  const [showCreateStrategy, setShowCreateStrategy] = useState(false);
  const [showEventLogs, setShowEventLogs] = useState(false);
  const [eventLogsStrategyId, setEventLogsStrategyId] = useState<number | null>(null);
  const [eventLogsStrategyName, setEventLogsStrategyName] = useState<string>('');
  const [showSettings, setShowSettings] = useState(false);
  const [settingsStrategyId, setSettingsStrategyId] = useState<number | null>(null);
  const [settingsStrategyName, setSettingsStrategyName] = useState<string>('');
  const [showTypedSettings, setShowTypedSettings] = useState(false);
  const [selectedTypedStrategy, setSelectedTypedStrategy] = useState<Strategy | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [activeSymbols] = useState<string[]>(['BTC/USD', 'AAPL', 'TSLA', 'SPY']);

  useEffect(() => {
    fetchStrategies();
    fetchAccountData();
  }, []);

  useEffect(() => {
    if (selectedStrategy) {
      fetchPerformance(selectedStrategy);
      fetchChartData(selectedStrategy);
      fetchPositions(selectedStrategy);
      fetchTrades(selectedStrategy);
    }
  }, [selectedStrategy]);

  const fetchStrategies = async () => {
    try {
      const strategiesData = await apiV2.getStrategies();
      console.log('Fetched strategies from v2 API:', strategiesData);
      
      setStrategies(strategiesData);
      if (strategiesData.length > 0 && !selectedStrategy) {
        setSelectedStrategy(strategiesData[0].id);
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

  const fetchAccountData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/trading/account`);
      setAccountData(response.data);
    } catch (error) {
      console.error('Error fetching account data:', error);
    }
  };

  const fetchPositions = async (strategyId: number) => {
    try {
      const response = await axios.get(`${API_BASE}/trading/positions/${strategyId}`);
      setPositions(response.data);
    } catch (error) {
      console.error('Error fetching positions:', error);
    }
  };

  const fetchTrades = async (strategyId: number) => {
    try {
      const response = await axios.get(`${API_BASE}/trading/trades/${strategyId}`);
      setTrades(response.data);
    } catch (error) {
      console.error('Error fetching trades:', error);
    }
  };

  const startStrategy = async (strategyId: number) => {
    try {
      await apiV2.startStrategy(strategyId);
      fetchStrategies(); // Refresh strategies
    } catch (error) {
      console.error('Error starting strategy:', error);
    }
  };

  const stopStrategy = async (strategyId: number) => {
    try {
      await apiV2.stopStrategy(strategyId);
      fetchStrategies(); // Refresh strategies
    } catch (error) {
      console.error('Error stopping strategy:', error);
    }
  };

  const createStrategy = async (strategyData: CreateStrategyData) => {
    try {
      // Still using axios for create strategy since apiV2 might not have this yet
      const response = await axios.post(`${API_BASE}/strategies/`, strategyData);
      fetchStrategies(); // Refresh the entire list to get proper v2 format
      setShowCreateStrategy(false);
    } catch (error) {
      console.error('Error creating strategy:', error);
    }
  };

  const deleteStrategy = async (strategyId: number) => {
    try {
      // Still using axios for delete strategy since apiV2 might not have this yet
      await axios.delete(`${API_BASE}/strategies/${strategyId}`);
      if (selectedStrategy === strategyId) {
        setSelectedStrategy(null);
      }
      fetchStrategies(); // Refresh the entire list
    } catch (error) {
      console.error('Error deleting strategy:', error);
    }
  };

  const showStrategyLogs = (strategyId: number, strategyName: string) => {
    setEventLogsStrategyId(strategyId);
    setEventLogsStrategyName(strategyName);
    setShowEventLogs(true);
  };

  const showStrategySettings = (strategyId: number, strategyName: string) => {
    const strategy = strategies.find(s => s.id === strategyId);
    if (strategy) {
      setSelectedTypedStrategy(strategy);
      setShowTypedSettings(true);
    } else {
      // Fallback to old settings modal
      setSettingsStrategyId(strategyId);
      setSettingsStrategyName(strategyName);
      setShowSettings(true);
    }
  };

  const closeTypedSettings = () => {
    setSelectedTypedStrategy(null);
    setShowTypedSettings(false);
  };

  const onTypedSettingsUpdated = () => {
    fetchStrategies(); // Refresh strategies after settings update
  };

  const handleSyncAllCapitals = async () => {
    try {
      setSyncing(true);
      const result = await apiV2.syncAllStrategiesCapital();
      alert(`✅ Account Sync Complete!\n${result.message}`);
      await fetchStrategies(); // Refresh to show updated capitals
    } catch (err) {
      alert(`❌ Sync Failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setSyncing(false);
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

      <PriceTicker symbols={activeSymbols} refreshInterval={30000} />

      <div className="dashboard-controls">
        <button onClick={() => setShowCreateStrategy(true)} className="btn btn-primary">
          + Create Strategy
        </button>
        <button 
          onClick={() => setShowBacktest(true)} 
          className="btn btn-secondary"
          disabled={!selectedStrategy}
        >
          📊 Backtest
        </button>
        <button 
          onClick={handleSyncAllCapitals} 
          className="btn btn-secondary"
          disabled={syncing}
        >
          {syncing ? '🔄 Syncing...' : '🔄 Sync with Alpaca'}
        </button>
        <button 
          onClick={() => window.open('http://localhost:8000/docs', '_blank')} 
          className="btn btn-secondary"
        >
          🔧 API Docs
        </button>
      </div>

      <div className="dashboard-content">
        <div className="left-column">
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
                  onDelete={() => deleteStrategy(strategy.id)}
                  onViewLogs={() => showStrategyLogs(strategy.id, strategy.name)}
                  onViewSettings={() => showStrategySettings(strategy.id, strategy.name)}
                />
              ))
            )}
          </div>

          <AccountInfo accountData={accountData} loading={!accountData} />
        </div>

        <div className="center-column">
          <div className="performance-panel">
            {selectedStrategy ? (
              <>
                <h2>📈 Performance Metrics</h2>
                <div className="metrics-grid">
                  {(() => {
                    const strategy = strategies.find(s => s.id === selectedStrategy);
                    if (!strategy) return null;
                    
                    const totalPnL = strategy.current_capital - strategy.initial_capital;
                    const roiPercentage = strategy.initial_capital > 0 
                      ? (totalPnL / strategy.initial_capital) * 100 
                      : 0;
                    
                    return (
                      <>
                        <div className="metric-card">
                          <h3>ROI</h3>
                          <p className={roiPercentage >= 0 ? 'positive' : 'negative'}>
                            {roiPercentage.toFixed(2)}%
                          </p>
                        </div>
                        <div className="metric-card">
                          <h3>Total P&L</h3>
                          <p className={totalPnL >= 0 ? 'positive' : 'negative'}>
                            ${totalPnL.toFixed(2)}
                          </p>
                        </div>
                        <div className="metric-card">
                          <h3>Win Rate</h3>
                          <p>{performance?.win_rate?.toFixed(1) || '0.0'}%</p>
                        </div>
                        <div className="metric-card">
                          <h3>Total Trades</h3>
                          <p>{performance?.total_trades || 0}</p>
                        </div>
                        <div className="metric-card">
                          <h3>Sharpe Ratio</h3>
                          <p>{performance?.sharpe_ratio?.toFixed(3) || 'N/A'}</p>
                        </div>
                        <div className="metric-card">
                          <h3>Max Drawdown</h3>
                          <p>{performance?.max_drawdown?.toFixed(2) || 'N/A'}%</p>
                        </div>
                      </>
                    );
                  })()}
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

        <div className="right-column">
          <RiskManagementPanel 
            strategyId={selectedStrategy}
            refreshInterval={30000}
          />
          
          <PositionsPanel 
            positions={positions} 
            loading={selectedStrategy ? false : true} 
          />
          
          <EnhancedTradesPanel 
            trades={trades} 
            loading={selectedStrategy ? false : true} 
          />
          
          {selectedStrategy && (
            <TradeAnalytics 
              trades={trades}
              currentCapital={strategies.find(s => s.id === selectedStrategy)?.current_capital || 0}
              initialCapital={strategies.find(s => s.id === selectedStrategy)?.initial_capital || 0}
            />
          )}
        </div>
      </div>

      {showBacktest && selectedStrategy && (
        <BacktestModal
          strategyId={selectedStrategy}
          onClose={() => setShowBacktest(false)}
        />
      )}
      
      {showCreateStrategy && (
        <CreateStrategyModal
          onClose={() => setShowCreateStrategy(false)}
          onCreate={createStrategy}
        />
      )}
      
      {showEventLogs && eventLogsStrategyId && (
        <StrategyEventLogsModal
          isOpen={showEventLogs}
          onClose={() => setShowEventLogs(false)}
          strategyId={eventLogsStrategyId}
          strategyName={eventLogsStrategyName}
        />
      )}

      {showSettings && settingsStrategyId && (
        <StrategySettingsModal
          isOpen={showSettings}
          onClose={() => setShowSettings(false)}
          strategyId={settingsStrategyId}
          strategyName={settingsStrategyName}
        />
      )}

      {/* Typed Settings Modal */}
      {selectedTypedStrategy && (
        <TypedSettingsModal
          strategy={selectedTypedStrategy}
          isOpen={showTypedSettings}
          onClose={closeTypedSettings}
          onSettingsUpdated={onTypedSettingsUpdated}
        />
      )}
    </div>
  );
};

export default Dashboard;