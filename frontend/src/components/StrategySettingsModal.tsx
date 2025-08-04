import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_CONFIG } from '../config/constants';

interface SettingValue {
  value: any;
  type: string;
  description: string;
  default_value?: any;
  is_required: boolean;
  created_at: string;
  updated_at: string;
}

interface StrategySettings {
  strategy_id: number;
  strategy_name: string;
  strategy_type: string;
  settings: Record<string, SettingValue>;
}

interface StrategySettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  strategyId: number;
  strategyName: string;
}

const StrategySettingsModal: React.FC<StrategySettingsModalProps> = ({
  isOpen,
  onClose,
  strategyId,
  strategyName
}) => {
  const [settings, setSettings] = useState<StrategySettings | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editedSettings, setEditedSettings] = useState<Record<string, any>>({});

  useEffect(() => {
    if (isOpen && strategyId) {
      fetchSettings();
    }
  }, [isOpen, strategyId]);

  const fetchSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_CONFIG.BASE_URL}/strategies/${strategyId}/settings`);
      setSettings(response.data);
      
      // Initialize edited settings with current values
      const initialEdited: Record<string, any> = {};
      Object.entries(response.data.settings).forEach(([key, settingValue]) => {
        initialEdited[key] = (settingValue as SettingValue).value;
      });
      setEditedSettings(initialEdited);
    } catch (error) {
      console.error('Error fetching settings:', error);
      setError('Failed to load strategy settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSettingChange = (key: string, value: any, type: string) => {
    let parsedValue = value;
    
    // Type conversion based on setting type
    try {
      switch (type) {
        case 'integer':
          parsedValue = parseInt(value, 10);
          if (isNaN(parsedValue)) throw new Error('Invalid integer');
          break;
        case 'float':
          parsedValue = parseFloat(value);
          if (isNaN(parsedValue)) throw new Error('Invalid float');
          break;
        case 'boolean':
          parsedValue = value === 'true' || value === true;
          break;
        case 'json':
          if (typeof value === 'string') {
            parsedValue = JSON.parse(value);
          }
          break;
        case 'string':
        default:
          parsedValue = String(value);
          break;
      }
    } catch (error) {
      console.error(`Error parsing ${key}:`, error);
      return; // Don't update if parsing fails
    }
    
    setEditedSettings(prev => ({
      ...prev,
      [key]: parsedValue
    }));
  };

  const handleSave = async () => {
    if (!settings) return;
    
    setSaving(true);
    setError(null);
    
    try {
      // Update each modified setting
      const updatePromises = Object.entries(editedSettings).map(async ([key, value]) => {
        const originalSetting = settings.settings[key];
        if (originalSetting && originalSetting.value !== value) {
          return axios.put(`${API_CONFIG.BASE_URL}/strategies/${strategyId}/settings/${key}`, {
            key,
            value,
            setting_type: originalSetting.type,
            description: originalSetting.description,
            is_required: originalSetting.is_required
          });
        }
      });
      
      await Promise.all(updatePromises.filter(Boolean));
      
      // Refresh settings to show updated values
      await fetchSettings();
      
      alert('Settings updated successfully!');
    } catch (error) {
      console.error('Error saving settings:', error);
      setError('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const renderSettingInput = (key: string, setting: SettingValue) => {
    const currentValue = editedSettings[key] ?? setting.value;
    
    switch (setting.type) {
      case 'boolean':
        return (
          <select
            value={currentValue ? 'true' : 'false'}
            onChange={(e) => handleSettingChange(key, e.target.value === 'true', 'boolean')}
            className="form-control"
          >
            <option value="true">True</option>
            <option value="false">False</option>
          </select>
        );
        
      case 'integer':
        return (
          <input
            type="number"
            step="1"
            value={currentValue}
            onChange={(e) => handleSettingChange(key, e.target.value, 'integer')}
            className="form-control"
          />
        );
        
      case 'float':
        return (
          <input
            type="number"
            step="any"
            value={currentValue}
            onChange={(e) => handleSettingChange(key, e.target.value, 'float')}
            className="form-control"
          />
        );
        
      case 'json':
        return (
          <textarea
            value={JSON.stringify(currentValue, null, 2)}
            onChange={(e) => handleSettingChange(key, e.target.value, 'json')}
            className="form-control"
            rows={4}
            style={{ fontFamily: 'monospace', fontSize: '12px' }}
          />
        );
        
      case 'string':
      default:
        return (
          <input
            type="text"
            value={currentValue}
            onChange={(e) => handleSettingChange(key, e.target.value, 'string')}
            className="form-control"
          />
        );
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div className="modal-content" style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '24px',
        maxWidth: '800px',
        maxHeight: '80vh',
        width: '90%',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div className="modal-header" style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
          paddingBottom: '15px',
          borderBottom: '1px solid #eee'
        }}>
          <h2 style={{ margin: 0, color: '#333' }}>
            ⚙️ Settings: {strategyName}
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#999'
            }}
          >
            ×
          </button>
        </div>

        <div className="modal-body" style={{
          flex: 1,
          overflow: 'auto',
          marginBottom: '20px'
        }}>
          {loading && (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <p>Loading settings...</p>
            </div>
          )}

          {error && (
            <div style={{
              backgroundColor: '#f8d7da',
              color: '#721c24',
              padding: '12px',
              borderRadius: '4px',
              marginBottom: '16px'
            }}>
              {error}
            </div>
          )}

          {settings && (
            <div>
              <div style={{
                backgroundColor: '#f8f9fa',
                padding: '12px',
                borderRadius: '4px',
                marginBottom: '20px',
                fontSize: '14px'
              }}>
                <strong>Strategy Type:</strong> {settings.strategy_type}
              </div>

              <div className="settings-form">
                {Object.entries(settings.settings).map(([key, setting]) => (
                  <div key={key} style={{
                    marginBottom: '20px',
                    padding: '16px',
                    border: '1px solid #ddd',
                    borderRadius: '4px'
                  }}>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '8px'
                    }}>
                      <label style={{
                        fontWeight: 'bold',
                        color: '#333',
                        fontSize: '14px'
                      }}>
                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        {setting.is_required && <span style={{ color: 'red' }}> *</span>}
                      </label>
                      <span style={{
                        backgroundColor: '#e9ecef',
                        padding: '2px 6px',
                        borderRadius: '3px',
                        fontSize: '12px',
                        color: '#6c757d'
                      }}>
                        {setting.type}
                      </span>
                    </div>
                    
                    {renderSettingInput(key, setting)}
                    
                    {setting.description && (
                      <div style={{
                        fontSize: '12px',
                        color: '#6c757d',
                        marginTop: '4px'
                      }}>
                        {setting.description}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer" style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '12px',
          paddingTop: '15px',
          borderTop: '1px solid #eee'
        }}>
          <button
            onClick={onClose}
            disabled={saving}
            style={{
              padding: '8px 16px',
              border: '1px solid #ddd',
              backgroundColor: 'white',
              color: '#333',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || loading}
            style={{
              padding: '8px 16px',
              border: 'none',
              backgroundColor: '#007bff',
              color: 'white',
              borderRadius: '4px',
              cursor: saving ? 'not-allowed' : 'pointer',
              opacity: saving ? 0.6 : 1
            }}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default StrategySettingsModal;