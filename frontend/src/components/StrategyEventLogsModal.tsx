import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './StrategyEventLogsModal.css';

interface EventLog {
  id: number;
  level: string;
  event_type: string;
  message: string;
  details?: any;
  timestamp: string;
}

interface EventSummary {
  strategy_id: number;
  total_events: number;
  event_counts: Record<string, number>;
  level_counts: Record<string, number>;
  latest_events: Record<string, EventLog>;
  last_activity?: string;
}

interface StrategyEventLogsModalProps {
  isOpen: boolean;
  onClose: () => void;
  strategyId: number;
  strategyName: string;
}

const API_BASE = 'http://localhost:8000/api';

const StrategyEventLogsModal: React.FC<StrategyEventLogsModalProps> = ({
  isOpen,
  onClose,
  strategyId,
  strategyName
}) => {
  const [events, setEvents] = useState<EventLog[]>([]);
  const [summary, setSummary] = useState<EventSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedLevel, setSelectedLevel] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'recent' | 'summary'>('recent');

  useEffect(() => {
    if (isOpen) {
      fetchEvents();
      fetchSummary();
    }
  }, [isOpen, strategyId, selectedLevel, selectedType]);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('limit', '100');
      
      if (selectedLevel !== 'all') {
        params.append('level', selectedLevel);
      }
      if (selectedType !== 'all') {
        params.append('event_type', selectedType);
      }

      const response = await axios.get(`${API_BASE}/strategy-events/strategy/${strategyId}?${params}`);
      setEvents(response.data);
    } catch (error) {
      console.error('Error fetching events:', error);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await axios.get(`${API_BASE}/strategy-events/strategy/${strategyId}/summary`);
      setSummary(response.data);
    } catch (error) {
      console.error('Error fetching summary:', error);
    }
  };

  const clearOldEvents = async () => {
    try {
      await axios.delete(`${API_BASE}/strategy-events/strategy/${strategyId}?keep_recent=20`);
      fetchEvents();
      fetchSummary();
    } catch (error) {
      console.error('Error clearing events:', error);
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'debug': return '🔍';
      case 'info': return 'ℹ️';
      case 'warn': return '⚠️';
      case 'error': return '❌';
      case 'critical': return '🚨';
      default: return '📝';
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'debug': return '#6b7280';
      case 'info': return '#3b82f6';
      case 'warn': return '#f59e0b';
      case 'error': return '#ef4444';
      case 'critical': return '#dc2626';
      default: return '#6b7280';
    }
  };

  const getEventTypeIcon = (eventType: string) => {
    switch (eventType) {
      case 'strategy_lifecycle': return '🔄';
      case 'trade_check': return '🔍';
      case 'signal_generated': return '📊';
      case 'order_placed': return '📝';
      case 'order_filled': return '✅';
      case 'risk_alert': return '⚠️';
      case 'performance_update': return '📈';
      case 'market_data': return '💹';
      case 'portfolio_rebalance': return '⚖️';
      default: return '📋';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const formatEventType = (eventType: string) => {
    return eventType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal event-logs-modal">
        <div className="modal-header">
          <h2>📋 Event Logs - {strategyName}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="event-logs-controls">
          <div className="view-mode-tabs">
            <button 
              className={viewMode === 'recent' ? 'active' : ''}
              onClick={() => setViewMode('recent')}
            >
              Recent Events
            </button>
            <button 
              className={viewMode === 'summary' ? 'active' : ''}
              onClick={() => setViewMode('summary')}
            >
              Summary
            </button>
          </div>

          {viewMode === 'recent' && (
            <div className="filters">
              <select 
                value={selectedLevel} 
                onChange={(e) => setSelectedLevel(e.target.value)}
                className="filter-select"
              >
                <option value="all">All Levels</option>
                <option value="debug">Debug</option>
                <option value="info">Info</option>
                <option value="warn">Warning</option>
                <option value="error">Error</option>
                <option value="critical">Critical</option>
              </select>

              <select 
                value={selectedType} 
                onChange={(e) => setSelectedType(e.target.value)}
                className="filter-select"
              >
                <option value="all">All Types</option>
                <option value="strategy_lifecycle">Lifecycle</option>
                <option value="trade_check">Trade Checks</option>
                <option value="signal_generated">Signals</option>
                <option value="order_placed">Orders</option>
                <option value="risk_alert">Risk Alerts</option>
                <option value="performance_update">Performance</option>
                <option value="market_data">Market Data</option>
              </select>

              <button 
                className="clear-btn"
                onClick={clearOldEvents}
                title="Clear old events (keep 20 most recent)"
              >
                🗑️ Clear Old
              </button>
            </div>
          )}
        </div>

        <div className="modal-body">
          {viewMode === 'recent' ? (
            <div className="events-list">
              {loading ? (
                <div className="loading-state">Loading events...</div>
              ) : events.length === 0 ? (
                <div className="empty-state">
                  <p>No events found for the selected filters.</p>
                  <p>Events will appear here as the strategy runs and performs actions.</p>
                </div>
              ) : (
                events.map((event) => (
                  <div key={event.id} className={`event-item level-${event.level}`}>
                    <div className="event-header">
                      <span className="event-icon">
                        {getEventTypeIcon(event.event_type)}
                      </span>
                      <span className="event-type">
                        {formatEventType(event.event_type)}
                      </span>
                      <span 
                        className="event-level"
                        style={{ color: getLevelColor(event.level) }}
                      >
                        {getLevelIcon(event.level)} {event.level.toUpperCase()}
                      </span>
                      <span className="event-time">
                        {formatTimestamp(event.timestamp)}
                      </span>
                    </div>
                    <div className="event-message">
                      {event.message}
                    </div>
                    {event.details && (
                      <div className="event-details">
                        <pre>{JSON.stringify(event.details, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          ) : (
            <div className="events-summary">
              {summary ? (
                <>
                  <div className="summary-stats">
                    <div className="stat-card">
                      <h4>Total Events</h4>
                      <p className="stat-value">{summary.total_events}</p>
                    </div>
                    <div className="stat-card">
                      <h4>Last Activity</h4>
                      <p className="stat-value">
                        {summary.last_activity 
                          ? formatTimestamp(summary.last_activity)
                          : 'No recent activity'
                        }
                      </p>
                    </div>
                  </div>

                  <div className="summary-section">
                    <h4>Events by Level</h4>
                    <div className="level-counts">
                      {Object.entries(summary.level_counts).map(([level, count]) => (
                        count > 0 && (
                          <div key={level} className="count-item">
                            <span style={{ color: getLevelColor(level) }}>
                              {getLevelIcon(level)} {level.toUpperCase()}
                            </span>
                            <span className="count">{count}</span>
                          </div>
                        )
                      ))}
                    </div>
                  </div>

                  <div className="summary-section">
                    <h4>Events by Type</h4>
                    <div className="type-counts">
                      {Object.entries(summary.event_counts).map(([type, count]) => (
                        <div key={type} className="count-item">
                          <span>
                            {getEventTypeIcon(type)} {formatEventType(type)}
                          </span>
                          <span className="count">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="summary-section">
                    <h4>Latest Activity by Type</h4>
                    <div className="latest-events">
                      {Object.entries(summary.latest_events).map(([type, event]) => (
                        <div key={type} className="latest-event">
                          <div className="latest-event-type">
                            {getEventTypeIcon(type)} {formatEventType(type)}
                          </div>
                          <div className="latest-event-message">{event.message}</div>
                          <div className="latest-event-time">
                            {formatTimestamp(event.timestamp)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="loading-state">Loading summary...</div>
              )}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
          <button 
            className="btn btn-primary" 
            onClick={() => {
              fetchEvents();
              fetchSummary();
            }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>
    </div>
  );
};

export default StrategyEventLogsModal;