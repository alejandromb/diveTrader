import React, { useState } from 'react';
import { DEFAULT_PORTFOLIO, DEFAULT_STRATEGY_CONFIG, INVESTMENT_DEFAULTS } from '../config/constants';

interface CreateStrategyModalProps {
  onClose: () => void;
  onCreate: (strategyData: CreateStrategyData) => void;
}

export interface CreateStrategyData {
  name: string;
  strategy_type: 'btc_scalping' | 'portfolio_distributor';
  initial_capital: number;
  config: {
    // BTC Scalping Config
    btc_scalping?: {
      risk_per_trade: number;
      max_daily_trades: number;
      stop_loss_percent: number;
      take_profit_percent: number;
    };
    // Portfolio Distributor Config
    portfolio_distributor?: {
      symbols: string[];
      allocation_weights: Record<string, number>;
      investment_frequency: 'weekly' | 'monthly';
      investment_amount: number;
      rebalance_threshold: number;
    };
  };
}

const CreateStrategyModal: React.FC<CreateStrategyModalProps> = ({ onClose, onCreate }) => {
  const [formData, setFormData] = useState<CreateStrategyData>({
    name: '',
    strategy_type: 'btc_scalping',
    initial_capital: INVESTMENT_DEFAULTS.INITIAL_CAPITAL,
    config: {}
  });

  const [btcConfig, setBtcConfig] = useState(DEFAULT_STRATEGY_CONFIG.BTC_SCALPING);

  const [portfolioConfig, setPortfolioConfig] = useState({
    symbols: DEFAULT_PORTFOLIO.SYMBOLS,
    investment_frequency: DEFAULT_STRATEGY_CONFIG.PORTFOLIO_DISTRIBUTOR.investment_frequency,
    investment_amount: DEFAULT_STRATEGY_CONFIG.PORTFOLIO_DISTRIBUTOR.investment_amount,
    rebalance_threshold: DEFAULT_STRATEGY_CONFIG.PORTFOLIO_DISTRIBUTOR.rebalance_threshold
  });

  const [portfolioSymbolsText, setPortfolioSymbolsText] = useState(DEFAULT_PORTFOLIO.SYMBOLS_TEXT);
  const [portfolioWeightsText, setPortfolioWeightsText] = useState(DEFAULT_PORTFOLIO.WEIGHTS_TEXT);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const finalData = { ...formData };
    
    if (formData.strategy_type === 'btc_scalping') {
      finalData.config = { btc_scalping: btcConfig };
    } else {
      // Parse portfolio symbols and weights
      const symbols = portfolioSymbolsText.split(',').map(s => s.trim().toUpperCase());
      const weights = portfolioWeightsText.split(',').map(w => parseFloat(w.trim()));
      
      const allocation_weights: Record<string, number> = {};
      symbols.forEach((symbol, index) => {
        allocation_weights[symbol] = weights[index] || 25; // Default to 25% if weight missing
      });
      
      finalData.config = {
        portfolio_distributor: {
          ...portfolioConfig,
          symbols,
          allocation_weights
        }
      };
    }
    
    onCreate(finalData);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content create-strategy-modal">
        <div className="modal-header">
          <h2>🚀 Create New Strategy</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-body">
          {/* Basic Strategy Info */}
          <div className="form-section">
            <h3>Strategy Details</h3>
            
            <div className="form-group">
              <label>Strategy Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="My Trading Strategy"
                required
              />
            </div>
            
            <div className="form-group">
              <label>Strategy Type</label>
              <select 
                value={formData.strategy_type} 
                onChange={(e) => setFormData({...formData, strategy_type: e.target.value as any})}
              >
                <option value="btc_scalping">₿ BTC Scalping</option>
                <option value="portfolio_distributor">📊 Portfolio Distributor</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>Initial Capital</label>
              <input
                type="number"
                value={formData.initial_capital}
                onChange={(e) => setFormData({...formData, initial_capital: parseFloat(e.target.value)})}
                min="100"
                step="100"
                required
              />
            </div>
          </div>

          {/* BTC Scalping Configuration */}
          {formData.strategy_type === 'btc_scalping' && (
            <div className="form-section">
              <h3>₿ BTC Scalping Settings</h3>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Risk Per Trade (%)</label>
                  <input
                    type="number"
                    value={btcConfig.risk_per_trade}
                    onChange={(e) => setBtcConfig({...btcConfig, risk_per_trade: parseFloat(e.target.value)})}
                    min="0.1"
                    max="10"
                    step="0.1"
                  />
                </div>
                
                <div className="form-group">
                  <label>Max Daily Trades</label>
                  <input
                    type="number"
                    value={btcConfig.max_daily_trades}
                    onChange={(e) => setBtcConfig({...btcConfig, max_daily_trades: parseInt(e.target.value)})}
                    min="1"
                    max="100"
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Stop Loss (%)</label>
                  <input
                    type="number"
                    value={btcConfig.stop_loss_percent}
                    onChange={(e) => setBtcConfig({...btcConfig, stop_loss_percent: parseFloat(e.target.value)})}
                    min="0.1"
                    max="10"
                    step="0.1"
                  />
                </div>
                
                <div className="form-group">
                  <label>Take Profit (%)</label>
                  <input
                    type="number"
                    value={btcConfig.take_profit_percent}
                    onChange={(e) => setBtcConfig({...btcConfig, take_profit_percent: parseFloat(e.target.value)})}
                    min="0.1"
                    max="20"
                    step="0.1"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Portfolio Distributor Configuration */}
          {formData.strategy_type === 'portfolio_distributor' && (
            <div className="form-section">
              <h3>📊 Portfolio Distribution Settings</h3>
              
              <div className="form-group">
                <label>Stock Symbols (comma-separated)</label>
                <input
                  type="text"
                  value={portfolioSymbolsText}
                  onChange={(e) => setPortfolioSymbolsText(e.target.value)}
                  placeholder={DEFAULT_PORTFOLIO.SYMBOLS.join(', ')}
                />
              </div>
              
              <div className="form-group">
                <label>Allocation Weights (%) (comma-separated)</label>
                <input
                  type="text"
                  value={portfolioWeightsText}
                  onChange={(e) => setPortfolioWeightsText(e.target.value)}
                  placeholder={DEFAULT_PORTFOLIO.WEIGHTS_TEXT}
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Investment Frequency</label>
                  <select 
                    value={portfolioConfig.investment_frequency}
                    onChange={(e) => setPortfolioConfig({...portfolioConfig, investment_frequency: e.target.value as any})}
                  >
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Investment Amount ($)</label>
                  <input
                    type="number"
                    value={portfolioConfig.investment_amount}
                    onChange={(e) => setPortfolioConfig({...portfolioConfig, investment_amount: parseFloat(e.target.value)})}
                    min="50"
                    step="50"
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label>Rebalance Threshold (%)</label>
                <input
                  type="number"
                  value={portfolioConfig.rebalance_threshold}
                  onChange={(e) => setPortfolioConfig({...portfolioConfig, rebalance_threshold: parseFloat(e.target.value)})}
                  min="1"
                  max="20"
                  step="1"
                />
                <small>Rebalance when allocation drifts by this percentage</small>
              </div>
            </div>
          )}

          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              🚀 Create Strategy
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateStrategyModal;