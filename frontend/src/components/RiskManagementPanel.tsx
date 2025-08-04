import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './RiskManagementPanel.css';

interface RiskAlert {
  type: string;
  severity: string;
  message: string;
  timestamp: string;
  data?: any;
}

interface RiskMetrics {
  drawdown_percent: number;
  daily_pnl: number;
  daily_loss_percent: number;
  portfolio_value: number;
}

interface RiskLimits {
  max_portfolio_risk: number;
  max_daily_loss: number;
  max_drawdown: number;
  max_position_size: number;
  max_correlation_exposure: number;
  min_cash_reserve: number;
  max_leverage: number;
  stop_loss_required: boolean;
  position_concentration_limit: number;
}

interface RiskSummary {
  strategy_id: number;
  risk_limits: RiskLimits;
  current_metrics: RiskMetrics;
  alerts: RiskAlert[];
  status: 'healthy' | 'warning' | 'critical';
}

interface RiskManagementPanelProps {
  strategyId: number | null;
  refreshInterval?: number;
}

const API_BASE = 'http://localhost:8000/api';

const RiskManagementPanel: React.FC<RiskManagementPanelProps> = ({ 
  strategyId, 
  refreshInterval = 30000 
}) => {
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [showLimitsModal, setShowLimitsModal] = useState(false);
  const [editingLimits, setEditingLimits] = useState<Partial<RiskLimits>>({});

  useEffect(() => {
    if (strategyId) {
      fetchRiskSummary();
      const interval = setInterval(fetchRiskSummary, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [strategyId, refreshInterval]);

  const fetchRiskSummary = async () => {
    if (!strategyId) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/risk/summary/${strategyId}`);
      setRiskSummary(response.data);
    } catch (error) {
      console.error('Error fetching risk summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateRiskLimits = async () => {
    if (!strategyId) return;

    try {
      await axios.put(`${API_BASE}/risk/limits/${strategyId}`, editingLimits);
      setShowLimitsModal(false);
      setEditingLimits({});
      fetchRiskSummary();
    } catch (error) {
      console.error('Error updating risk limits:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#10b981';
      case 'warning': return '#f59e0b';
      case 'critical': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'low': return '🟢';
      case 'medium': return '🟡';
      case 'high': return '🟠';
      case 'critical': return '🔴';
      default: return '⚪';
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInSeconds = Math.floor((now.getTime() - time.getTime()) / 1000);
    
    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  if (!strategyId) {
    return (
      <div className="risk-panel">
        <h3>⚠️ Risk Management</h3>
        <div className="empty-state">
          <p>Select a strategy to view risk metrics</p>
        </div>
      </div>
    );
  }

  return (
    <div className="risk-panel">
      <div className="risk-header">
        <h3>⚠️ Risk Management</h3>
        <div className="risk-status">
          <span 
            className="status-indicator"
            style={{ backgroundColor: getStatusColor(riskSummary?.status || 'unknown') }}
          />
          <span className="status-text">
            {riskSummary?.status?.toUpperCase() || 'LOADING'}
          </span>
        </div>
        <button 
          className="btn btn-small"
          onClick={() => {
            if (riskSummary) {
              setEditingLimits(riskSummary.risk_limits);
              setShowLimitsModal(true);
            }
          }}
        >
          ⚙️ Settings
        </button>
      </div>

      {loading && !riskSummary && (
        <div className="loading-state">Loading risk data...</div>
      )}

      {riskSummary && (
        <>
          <div className="risk-metrics">
            <div className="metric-row">
              <span className="metric-label">Drawdown:</span>
              <span className={`metric-value ${riskSummary.current_metrics.drawdown_percent > 10 ? 'negative' : ''}`}>
                {riskSummary.current_metrics.drawdown_percent.toFixed(2)}%
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Daily P&L:</span>
              <span className={`metric-value ${riskSummary.current_metrics.daily_pnl >= 0 ? 'positive' : 'negative'}`}>
                ${riskSummary.current_metrics.daily_pnl.toFixed(2)}
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Daily Loss %:</span>
              <span className="metric-value">
                {riskSummary.current_metrics.daily_loss_percent.toFixed(2)}%
              </span>
            </div>
            <div className="metric-row">
              <span className="metric-label">Portfolio Value:</span>
              <span className="metric-value">
                ${riskSummary.current_metrics.portfolio_value.toFixed(2)}
              </span>
            </div>
          </div>

          <div className="risk-alerts">
            <h4>Active Alerts ({riskSummary.alerts.length})</h4>
            {riskSummary.alerts.length === 0 ? (
              <div className="no-alerts">No active risk alerts ✅</div>
            ) : (
              <div className="alerts-list">
                {riskSummary.alerts.map((alert, index) => (
                  <div key={index} className={`alert alert-${alert.severity}`}>
                    <div className="alert-header">
                      <span className="alert-icon">
                        {getSeverityIcon(alert.severity)}
                      </span>
                      <span className="alert-type">{alert.type.replace('_', ' ').toUpperCase()}</span>
                      <span className="alert-time">{formatTimeAgo(alert.timestamp)}</span>
                    </div>
                    <div className="alert-message">{alert.message}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {showLimitsModal && (
        <div className="modal-overlay">
          <div className="modal risk-limits-modal">
            <div className="modal-header">
              <h3>Risk Limits Configuration</h3>
              <button 
                className="close-btn"
                onClick={() => setShowLimitsModal(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="limits-form">
                <div className="form-group">
                  <label>Max Portfolio Risk (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingLimits.max_portfolio_risk || ''}
                    onChange={(e) => setEditingLimits({
                      ...editingLimits,
                      max_portfolio_risk: parseFloat(e.target.value) || 0
                    })}
                  />
                </div>
                <div className="form-group">
                  <label>Max Daily Loss (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingLimits.max_daily_loss || ''}
                    onChange={(e) => setEditingLimits({
                      ...editingLimits,
                      max_daily_loss: parseFloat(e.target.value) || 0
                    })}
                  />
                </div>
                <div className="form-group">
                  <label>Max Drawdown (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingLimits.max_drawdown || ''}
                    onChange={(e) => setEditingLimits({
                      ...editingLimits,
                      max_drawdown: parseFloat(e.target.value) || 0
                    })}
                  />
                </div>
                <div className="form-group">
                  <label>Max Position Size (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingLimits.max_position_size || ''}
                    onChange={(e) => setEditingLimits({
                      ...editingLimits,
                      max_position_size: parseFloat(e.target.value) || 0
                    })}
                  />
                </div>
                <div className="form-group">
                  <label>Min Cash Reserve (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingLimits.min_cash_reserve || ''}
                    onChange={(e) => setEditingLimits({
                      ...editingLimits,
                      min_cash_reserve: parseFloat(e.target.value) || 0
                    })}
                  />
                </div>
                <div className="form-group">
                  <label>Max Leverage</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingLimits.max_leverage || ''}
                    onChange={(e) => setEditingLimits({
                      ...editingLimits,
                      max_leverage: parseFloat(e.target.value) || 0
                    })}
                  />
                </div>
                <div className="form-group checkbox-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={editingLimits.stop_loss_required || false}
                      onChange={(e) => setEditingLimits({
                        ...editingLimits,
                        stop_loss_required: e.target.checked
                      })}
                    />
                    Require Stop Loss Orders
                  </label>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowLimitsModal(false)}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary"
                onClick={updateRiskLimits}
              >
                Save Limits
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskManagementPanel;