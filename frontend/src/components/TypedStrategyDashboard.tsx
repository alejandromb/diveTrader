/**
 * Type-safe Strategy Dashboard using SQLModel v2 API
 * Demonstrates full TypeScript integration with the new backend
 */

import React, { useState, useEffect } from 'react';
import { 
  apiV2, 
  Strategy, 
  StrategyType, 
  strategyHelpers 
} from '../services/apiV2';
import TypedSettingsModal from './TypedSettingsModal';

export const TypedStrategyDashboard: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);

  // Load strategies on component mount
  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    try {
      setLoading(true);
      setError(null);
      const strategiesData = await apiV2.getStrategies();
      setStrategies(strategiesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load strategies');
    } finally {
      setLoading(false);
    }
  };

  const handleStartStrategy = async (strategy: Strategy) => {
    try {
      await apiV2.startStrategy(strategy.id);
      await loadStrategies(); // Refresh to get updated running status
    } catch (err) {
      alert(`Failed to start strategy: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleStopStrategy = async (strategy: Strategy) => {
    try {
      await apiV2.stopStrategy(strategy.id);
      await loadStrategies(); // Refresh to get updated running status
    } catch (err) {
      alert(`Failed to stop strategy: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const openSettings = (strategy: Strategy) => {
    setSelectedStrategy(strategy);
    setSettingsModalOpen(true);
  };

  const closeSettings = () => {
    setSelectedStrategy(null);
    setSettingsModalOpen(false);
  };

  const onSettingsUpdated = () => {
    loadStrategies(); // Refresh strategies after settings update
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="text-center mt-4 text-gray-600">Loading strategies...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <h3 className="font-bold">Error Loading Strategies</h3>
          <p>{error}</p>
          <button
            onClick={loadStrategies}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">
          Trading Strategies Dashboard
        </h1>
        <div className="flex items-center text-sm text-gray-600">
          <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
          SQLModel v2 API - Type Safe
        </div>
      </div>

      {strategies.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No strategies found</p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {strategies.map((strategy) => (
            <div
              key={strategy.id}
              className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden"
            >
              {/* Strategy Header */}
              <div className="p-4 border-b border-gray-200">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {strategy.name}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {strategyHelpers.formatStrategyType(strategy.strategy_type)}
                    </p>
                  </div>
                  <div className="flex items-center">
                    {strategy.is_running ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></div>
                        Running
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        <div className="w-2 h-2 bg-gray-500 rounded-full mr-1"></div>
                        Stopped
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Strategy Details */}
              <div className="p-4 space-y-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Initial Capital</p>
                    <p className="font-medium">${strategy.initial_capital.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Current Capital</p>
                    <p className="font-medium">${strategy.current_capital.toLocaleString()}</p>
                  </div>
                </div>

                <div className="text-sm">
                  <p className="text-gray-500">P&L</p>
                  <p className={`font-medium ${
                    strategy.current_capital >= strategy.initial_capital 
                      ? 'text-green-600' 
                      : 'text-red-600'
                  }`}>
                    ${(strategy.current_capital - strategy.initial_capital).toLocaleString()}
                    {' '}
                    ({(((strategy.current_capital - strategy.initial_capital) / strategy.initial_capital) * 100).toFixed(2)}%)
                  </p>
                </div>

                <div className="text-sm">
                  <p className="text-gray-500">Status</p>
                  <p className={`font-medium ${strategy.is_active ? 'text-green-600' : 'text-gray-600'}`}>
                    {strategy.is_active ? 'Active' : 'Inactive'}
                  </p>
                </div>

                {/* Strategy Type Specific Info */}
                {strategyHelpers.isBTCStrategy(strategy) && (
                  <div className="bg-orange-50 p-3 rounded-md">
                    <div className="flex items-center">
                      <span className="text-orange-600 text-xl mr-2">₿</span>
                      <div>
                        <p className="text-sm font-medium text-orange-900">Bitcoin Scalping</p>
                        <p className="text-xs text-orange-700">High-frequency BTC trading</p>
                      </div>
                    </div>
                  </div>
                )}

                {strategyHelpers.isPortfolioStrategy(strategy) && (
                  <div className="bg-blue-50 p-3 rounded-md">
                    <div className="flex items-center">
                      <span className="text-blue-600 text-xl mr-2">📊</span>
                      <div>
                        <p className="text-sm font-medium text-blue-900">Portfolio Distribution</p>
                        <p className="text-xs text-blue-700">Automated portfolio management</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="p-4 border-t border-gray-200 bg-gray-50">
                <div className="flex space-x-2">
                  {strategy.is_running ? (
                    <button
                      onClick={() => handleStopStrategy(strategy)}
                      className="flex-1 px-3 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                    >
                      Stop
                    </button>
                  ) : (
                    <button
                      onClick={() => handleStartStrategy(strategy)}
                      className="flex-1 px-3 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
                    >
                      Start
                    </button>
                  )}
                  
                  <button
                    onClick={() => openSettings(strategy)}
                    className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    Settings
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Typed Settings Modal */}
      {selectedStrategy && (
        <TypedSettingsModal
          strategy={selectedStrategy}
          isOpen={settingsModalOpen}
          onClose={closeSettings}
          onSettingsUpdated={onSettingsUpdated}
        />
      )}

      {/* API Status Footer */}
      <div className="mt-8 p-4 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex items-center">
          <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
          <div>
            <p className="text-sm font-medium text-green-900">
              Connected to SQLModel v2 API
            </p>
            <p className="text-xs text-green-700">
              Full type safety with automatic validation and TypeScript integration
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TypedStrategyDashboard;