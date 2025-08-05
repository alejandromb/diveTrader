/**
 * Type-safe Settings Modal using SQLModel v2 API
 * Full TypeScript integration with automatic validation
 */

import React, { useState, useEffect } from 'react';
import { 
  apiV2, 
  strategyHelpers 
} from '../services/apiV2';
import type { 
  Strategy, 
  StrategyType, 
  BTCScalpingSettings, 
  PortfolioDistributorSettings
} from '../services/apiV2';
import { InvestmentFrequency } from '../types/api';

interface TypedSettingsModalProps {
  strategy: Strategy;
  isOpen: boolean;
  onClose: () => void;
  onSettingsUpdated: () => void;
}

export const TypedSettingsModal: React.FC<TypedSettingsModalProps> = ({
  strategy,
  isOpen,
  onClose,
  onSettingsUpdated
}) => {
  // State for different strategy types
  const [btcSettings, setBtcSettings] = useState<BTCScalpingSettings | null>(null);
  const [portfolioSettings, setPortfolioSettings] = useState<PortfolioDistributorSettings | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Load settings when modal opens
  useEffect(() => {
    if (isOpen && strategy) {
      loadSettings();
    }
  }, [isOpen, strategy]);

  const loadSettings = async () => {
    setLoading(true);
    setError(null);
    
    try {
      if (strategyHelpers.isBTCStrategy(strategy)) {
        const settings = await apiV2.getBTCSettings(strategy.id);
        setBtcSettings(settings);
      } else if (strategyHelpers.isPortfolioStrategy(strategy)) {
        const settings = await apiV2.getPortfolioSettings(strategy.id);
        setPortfolioSettings(settings);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    setError(null);

    try {
      if (btcSettings && strategyHelpers.isBTCStrategy(strategy)) {
        await apiV2.updateBTCSettings(strategy.id, btcSettings);
      } else if (portfolioSettings && strategyHelpers.isPortfolioStrategy(strategy)) {
        await apiV2.updatePortfolioSettings(strategy.id, portfolioSettings);
      }
      
      onSettingsUpdated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  // BTC Settings Form Component
  const BTCSettingsForm: React.FC = () => {
    if (!btcSettings) return null;

    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">BTC Scalping Settings</h3>
        
        {/* Position Size */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Position Size
          </label>
          <input
            type="number"
            step="0.001"
            min="0.001"
            max="1.0"
            value={btcSettings.position_size || 0.001}
            onChange={(e) => setBtcSettings({
              ...btcSettings,
              position_size: parseFloat(e.target.value)
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">Amount to invest per trade (0.001 - 1.0)</p>
        </div>

        {/* Take Profit */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Take Profit %
          </label>
          <input
            type="number"
            step="0.001"
            min="0.001"
            max="0.1"
            value={btcSettings.take_profit_pct || 0.002}
            onChange={(e) => setBtcSettings({
              ...btcSettings,
              take_profit_pct: parseFloat(e.target.value)
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">Profit target percentage (0.001 - 0.1)</p>
        </div>

        {/* Stop Loss */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Stop Loss %
          </label>
          <input
            type="number"
            step="0.001"
            min="0.001"
            max="0.1"
            value={btcSettings.stop_loss_pct || 0.001}
            onChange={(e) => setBtcSettings({
              ...btcSettings,
              stop_loss_pct: parseFloat(e.target.value)
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">Maximum loss percentage (0.001 - 0.1)</p>
        </div>

        {/* Technical Analysis Settings */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Short MA Periods
            </label>
            <input
              type="number"
              min="1"
              max="50"
              value={btcSettings.short_ma_periods || 3}
              onChange={(e) => setBtcSettings({
                ...btcSettings,
                short_ma_periods: parseInt(e.target.value)
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Long MA Periods
            </label>
            <input
              type="number"
              min="2"
              max="100"
              value={btcSettings.long_ma_periods || 5}
              onChange={(e) => setBtcSettings({
                ...btcSettings,
                long_ma_periods: parseInt(e.target.value)
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* AI Settings */}
        <div className="border-t pt-4">
          <div className="flex items-center mb-2">
            <input
              id="use-ai"
              type="checkbox"
              checked={btcSettings.use_ai_analysis || false}
              onChange={(e) => setBtcSettings({
                ...btcSettings,
                use_ai_analysis: e.target.checked
              })}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="use-ai" className="ml-2 block text-sm text-gray-900">
              Enable AI Analysis
            </label>
          </div>
          
          {btcSettings.use_ai_analysis && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                AI Confidence Threshold
              </label>
              <input
                type="number"
                step="0.1"
                min="0.1"
                max="1.0"
                value={btcSettings.ai_confidence_threshold || 0.7}
                onChange={(e) => setBtcSettings({
                  ...btcSettings,
                  ai_confidence_threshold: parseFloat(e.target.value)
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}
        </div>

        {/* Paper Trading */}
        <div className="flex items-center">
          <input
            id="paper-trading"
            type="checkbox"
            checked={btcSettings.paper_trading_mode || false}
            onChange={(e) => setBtcSettings({
              ...btcSettings,
              paper_trading_mode: e.target.checked
            })}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="paper-trading" className="ml-2 block text-sm text-gray-900">
            Paper Trading Mode
          </label>
        </div>
      </div>
    );
  };

  // Portfolio Settings Form Component  
  const PortfolioSettingsForm: React.FC = () => {
    if (!portfolioSettings) return null;

    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Portfolio Distributor Settings</h3>
        
        {/* Investment Amount */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Investment Amount ($)
          </label>
          <input
            type="number"
            min="1"
            value={portfolioSettings.investment_amount || 100}
            onChange={(e) => setPortfolioSettings({
              ...portfolioSettings,
              investment_amount: parseFloat(e.target.value)
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">Amount to invest per period</p>
        </div>

        {/* Investment Frequency */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Investment Frequency
          </label>
          <select
            value={portfolioSettings.investment_frequency || InvestmentFrequency.WEEKLY}
            onChange={(e) => setPortfolioSettings({
              ...portfolioSettings,
              investment_frequency: e.target.value as InvestmentFrequency
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={InvestmentFrequency.DAILY}>
              {strategyHelpers.formatInvestmentFrequency(InvestmentFrequency.DAILY)}
            </option>
            <option value={InvestmentFrequency.WEEKLY}>
              {strategyHelpers.formatInvestmentFrequency(InvestmentFrequency.WEEKLY)}
            </option>
            <option value={InvestmentFrequency.BIWEEKLY}>
              {strategyHelpers.formatInvestmentFrequency(InvestmentFrequency.BIWEEKLY)}
            </option>
            <option value={InvestmentFrequency.MONTHLY}>
              {strategyHelpers.formatInvestmentFrequency(InvestmentFrequency.MONTHLY)}
            </option>
          </select>
          <p className="text-xs text-gray-500 mt-1">How often to make investments</p>
        </div>

        {/* Symbols */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Symbols (comma-separated)
          </label>
          <input
            type="text"
            value={portfolioSettings.symbols || ''}
            onChange={(e) => setPortfolioSettings({
              ...portfolioSettings,
              symbols: e.target.value
            })}
            placeholder="SPY,AAPL,MSFT,GOOGL"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Rebalance Threshold */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Rebalance Threshold (%)
          </label>
          <input
            type="number"
            min="1"
            max="50"
            value={portfolioSettings.rebalance_threshold || 5}
            onChange={(e) => setPortfolioSettings({
              ...portfolioSettings,
              rebalance_threshold: parseFloat(e.target.value)
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">Trigger rebalancing when allocation drifts by this percentage</p>
        </div>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900">
            Settings - {strategy.name}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {loading && (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading settings...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            {strategyHelpers.isBTCStrategy(strategy) && <BTCSettingsForm />}
            {strategyHelpers.isPortfolioStrategy(strategy) && <PortfolioSettingsForm />}

            <div className="flex justify-end space-x-3 mt-6 pt-4 border-t">
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Cancel
              </button>
              <button
                onClick={saveSettings}
                disabled={saving}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Settings'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default TypedSettingsModal;