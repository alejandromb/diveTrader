/**
 * Type-safe Settings Modal using SQLModel v2 API
 * Full TypeScript integration with automatic validation
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Box,
  Paper,
  Grid,
  Alert,
  CircularProgress,
  Tooltip,
  IconButton
} from '@mui/material';
import { 
  HelpOutline,
  Close as CloseIcon 
} from '@mui/icons-material';
import { 
  apiV2, 
  strategyHelpers 
} from '../services/apiV2';
import type { 
  Strategy, 
  StrategyType, 
  BTCScalpingSettings, 
  PortfolioDistributorSettings
} from '../types/api';
import { InvestmentFrequency } from '../types/api';
import { TOOLTIPS } from '../config/tooltips';

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
      <Box>
        <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
          BTC Scalping Settings
        </Typography>
        
        {/* Budget Allocation Section */}
        <Paper elevation={1} sx={{ p: 3, mb: 3, bgcolor: 'primary.50' }}>
          <Typography variant="h6" gutterBottom sx={{ color: 'primary.main' }}>
            💰 Budget Allocation
          </Typography>
          
          {/* Max Positions */}
          <Box sx={{ mb: 2 }}>
            <Box display="flex" alignItems="center" mb={1}>
              <Typography variant="subtitle2">
                Maximum Concurrent Positions
              </Typography>
              <Tooltip title={TOOLTIPS.btc.maxPositions} arrow>
                <IconButton size="small" sx={{ ml: 1, p: 0.5 }}>
                  <HelpOutline sx={{ fontSize: 16, color: 'primary.main' }} />
                </IconButton>
              </Tooltip>
            </Box>
            <TextField
              type="number"
              size="small"
              fullWidth
              inputProps={{ min: 1, max: 20 }}
              value={btcSettings.max_positions || 5}
              onChange={(e) => setBtcSettings({
                ...btcSettings,
                max_positions: parseInt(e.target.value)
              })}
              helperText="How many BTC positions this strategy can hold at once"
            />
          </Box>
        </Paper>
        
        {/* Position Size */}
        <Box sx={{ mb: 2 }}>
          <Box display="flex" alignItems="center" mb={1}>
            <Typography variant="subtitle2">
              Position Size (BTC)
            </Typography>
            <Tooltip title={TOOLTIPS.btc.positionSize} arrow>
              <IconButton size="small" sx={{ ml: 1, p: 0.5 }}>
                <HelpOutline sx={{ fontSize: 16, color: 'primary.main' }} />
              </IconButton>
            </Tooltip>
          </Box>
          <TextField
            type="number"
            size="small"
            fullWidth
            inputProps={{ step: 0.001, min: 0.001, max: 1.0 }}
            value={btcSettings.position_size || 0.001}
            onChange={(e) => setBtcSettings({
              ...btcSettings,
              position_size: parseFloat(e.target.value)
            })}
            helperText="Amount to invest per trade (0.001 - 1.0)"
          />
        </Box>

        {/* Take Profit */}
        <Box sx={{ mb: 2 }}>
          <Box display="flex" alignItems="center" mb={1}>
            <Typography variant="subtitle2">
              Take Profit %
            </Typography>
            <Tooltip title={TOOLTIPS.btc.takeProfit} arrow>
              <IconButton size="small" sx={{ ml: 1, p: 0.5 }}>
                <HelpOutline sx={{ fontSize: 16, color: 'success.main' }} />
              </IconButton>
            </Tooltip>
          </Box>
          <TextField
            type="number"
            size="small"
            fullWidth
            inputProps={{ step: 0.001, min: 0.001, max: 0.1 }}
            value={btcSettings.take_profit_pct || 0.002}
            onChange={(e) => setBtcSettings({
              ...btcSettings,
              take_profit_pct: parseFloat(e.target.value)
            })}
            helperText="Profit target percentage (0.001 - 0.1)"
          />
        </Box>

        {/* Stop Loss */}
        <Box sx={{ mb: 2 }}>
          <Box display="flex" alignItems="center" mb={1}>
            <Typography variant="subtitle2">
              Stop Loss %
            </Typography>
            <Tooltip title={TOOLTIPS.btc.stopLoss} arrow>
              <IconButton size="small" sx={{ ml: 1, p: 0.5 }}>
                <HelpOutline sx={{ fontSize: 16, color: 'error.main' }} />
              </IconButton>
            </Tooltip>
          </Box>
          <TextField
            type="number"
            size="small"
            fullWidth
            inputProps={{ step: 0.001, min: 0.001, max: 0.1 }}
            value={btcSettings.stop_loss_pct || 0.001}
            onChange={(e) => setBtcSettings({
              ...btcSettings,
              stop_loss_pct: parseFloat(e.target.value)
            })}
            helperText="Maximum loss percentage (0.001 - 0.1)"
          />
        </Box>

        {/* Technical Analysis Settings */}
        <Paper elevation={1} sx={{ p: 3, mb: 3, bgcolor: 'info.50' }}>
          <Typography variant="h6" gutterBottom sx={{ color: 'info.main' }}>
            📈 Technical Analysis
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Box display="flex" alignItems="center" mb={1}>
                <Typography variant="subtitle2">
                  Short MA Periods (minutes)
                </Typography>
                <Tooltip title={TOOLTIPS.btc.shortMA} arrow>
                  <IconButton size="small" sx={{ ml: 1, p: 0.5 }}>
                    <HelpOutline sx={{ fontSize: 16, color: 'info.main' }} />
                  </IconButton>
                </Tooltip>
              </Box>
              <TextField
                type="number"
                size="small"
                fullWidth
                inputProps={{ min: 1, max: 50 }}
                value={btcSettings.short_ma_periods || 3}
                onChange={(e) => setBtcSettings({
                  ...btcSettings,
                  short_ma_periods: parseInt(e.target.value)
                })}
                helperText="1-50 minutes for moving average calculation"
              />
            </Grid>
            
            <Grid item xs={6}>
              <Box display="flex" alignItems="center" mb={1}>
                <Typography variant="subtitle2">
                  Long MA Periods (minutes)
                </Typography>
                <Tooltip title={TOOLTIPS.btc.longMA} arrow>
                  <IconButton size="small" sx={{ ml: 1, p: 0.5 }}>
                    <HelpOutline sx={{ fontSize: 16, color: 'info.main' }} />
                  </IconButton>
                </Tooltip>
              </Box>
              <TextField
                type="number"
                size="small"
                fullWidth
                inputProps={{ min: 2, max: 100 }}
                value={btcSettings.long_ma_periods || 5}
                onChange={(e) => setBtcSettings({
                  ...btcSettings,
                  long_ma_periods: parseInt(e.target.value)
                })}
                helperText="2-100 minutes for moving average calculation"
              />
            </Grid>
          </Grid>
        </Paper>

        {/* AI Settings */}
        <Paper elevation={1} sx={{ p: 3, mb: 3, bgcolor: 'warning.50' }}>
          <Typography variant="h6" gutterBottom sx={{ color: 'warning.main' }}>
            🤖 AI Analysis
          </Typography>
          
          <FormControlLabel
            control={
              <Checkbox
                checked={btcSettings.use_ai_analysis || false}
                onChange={(e) => setBtcSettings({
                  ...btcSettings,
                  use_ai_analysis: e.target.checked
                })}
              />
            }
            label="Enable AI Analysis"
            sx={{ mb: 2 }}
          />
          
          {btcSettings.use_ai_analysis && (
            <Box>
              <Box display="flex" alignItems="center" mb={1}>
                <Typography variant="subtitle2">
                  AI Confidence Threshold
                </Typography>
                <Tooltip title="Minimum AI confidence level required to execute trades. Higher values = more selective trading." arrow>
                  <IconButton size="small" sx={{ ml: 1, p: 0.5 }}>
                    <HelpOutline sx={{ fontSize: 16, color: 'warning.main' }} />
                  </IconButton>
                </Tooltip>
              </Box>
              <TextField
                type="number"
                size="small"
                fullWidth
                inputProps={{ step: 0.1, min: 0.1, max: 1.0 }}
                value={btcSettings.ai_confidence_threshold || 0.7}
                onChange={(e) => setBtcSettings({
                  ...btcSettings,
                  ai_confidence_threshold: parseFloat(e.target.value)
                })}
                helperText="0.1 - 1.0 (higher = more selective)"
              />
            </Box>
          )}
        </Paper>

        {/* Paper Trading */}
        <Paper elevation={1} sx={{ p: 3, bgcolor: 'secondary.50' }}>
          <Typography variant="h6" gutterBottom sx={{ color: 'secondary.main' }}>
            📝 Trading Mode
          </Typography>
          
          <Box display="flex" alignItems="center">
            <FormControlLabel
              control={
                <Checkbox
                  checked={btcSettings.paper_trading_mode || false}
                  onChange={(e) => setBtcSettings({
                    ...btcSettings,
                    paper_trading_mode: e.target.checked
                  })}
                />
              }
              label="Paper Trading Mode (Practice)"
            />
            <Tooltip title={TOOLTIPS.btc.paperTrading} arrow>
              <IconButton size="small" sx={{ ml: 1, p: 0.5 }}>
                <HelpOutline sx={{ fontSize: 16, color: 'secondary.main' }} />
              </IconButton>
            </Tooltip>
          </Box>
        </Paper>
      </Box>
    );
  };

  // Portfolio Settings Form Component  
  const PortfolioSettingsForm: React.FC = () => {
    if (!portfolioSettings) return null;

    return (
      <Box>
        <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
          Portfolio Distributor Settings
        </Typography>
        
        {/* Budget Allocation Section */}
        <Paper elevation={1} sx={{ p: 3, mb: 3, bgcolor: 'success.50' }}>
          <Typography variant="h6" gutterBottom sx={{ color: 'success.main' }}>
            💰 Budget Allocation
          </Typography>
          
          {/* Investment Amount */}
          <Box sx={{ mb: 2 }}>
            <Box display="flex" alignItems="center" mb={1}>
              <Typography variant="subtitle2">
                Total Investment Budget ($)
              </Typography>
              <Tooltip title={TOOLTIPS.portfolio.totalBudget} arrow>
                <IconButton size="small" sx={{ ml: 1, p: 0.5 }}>
                  <HelpOutline sx={{ fontSize: 16, color: 'success.main' }} />
                </IconButton>
              </Tooltip>
            </Box>
            <TextField
              type="number"
              size="small"
              fullWidth
              inputProps={{ min: 50, max: 10000 }}
              value={portfolioSettings.investment_amount || 100}
              onChange={(e) => setPortfolioSettings({
                ...portfolioSettings,
                investment_amount: parseFloat(e.target.value)
              })}
              helperText="Total amount this strategy can invest across all positions"
            />
          </Box>
          
          {/* Max Position Size */}
          <Box>
            <Box display="flex" alignItems="center" mb={1}>
              <Typography variant="subtitle2">
                Maximum Position Size ($)
              </Typography>
              <Tooltip title={TOOLTIPS.portfolio.maxPositionSize} arrow>
                <IconButton size="small" sx={{ ml: 1, p: 0.5 }}>
                  <HelpOutline sx={{ fontSize: 16, color: 'success.main' }} />
                </IconButton>
              </Tooltip>
            </Box>
            <TextField
              type="number"
              size="small"
              fullWidth
              inputProps={{ min: 10, max: 5000 }}
              value={portfolioSettings.max_position_size || 200}
              onChange={(e) => setPortfolioSettings({
                ...portfolioSettings,
                max_position_size: parseFloat(e.target.value)
              })}
              helperText="Maximum amount to invest in any single stock"
            />
          </Box>
        </Paper>
        
        {/* Investment Frequency */}
        <Box sx={{ mb: 2 }}>
          <Box display="flex" alignItems="center" mb={1}>
            <Typography variant="subtitle2">
              Investment Frequency
            </Typography>
            <Tooltip title={TOOLTIPS.portfolio.investmentFrequency} arrow>
              <IconButton size="small" sx={{ ml: 1, p: 0.5 }}>
                <HelpOutline sx={{ fontSize: 16, color: 'secondary.main' }} />
              </IconButton>
            </Tooltip>
          </Box>
          <FormControl fullWidth size="small">
            <Select
              value={portfolioSettings.investment_frequency || InvestmentFrequency.WEEKLY}
              onChange={(e) => setPortfolioSettings({
                ...portfolioSettings,
                investment_frequency: e.target.value as InvestmentFrequency
              })}
            >
              <MenuItem value={InvestmentFrequency.DAILY}>
                {strategyHelpers.formatInvestmentFrequency(InvestmentFrequency.DAILY)}
              </MenuItem>
              <MenuItem value={InvestmentFrequency.WEEKLY}>
                {strategyHelpers.formatInvestmentFrequency(InvestmentFrequency.WEEKLY)}
              </MenuItem>
              <MenuItem value={InvestmentFrequency.BIWEEKLY}>
                {strategyHelpers.formatInvestmentFrequency(InvestmentFrequency.BIWEEKLY)}
              </MenuItem>
              <MenuItem value={InvestmentFrequency.MONTHLY}>
                {strategyHelpers.formatInvestmentFrequency(InvestmentFrequency.MONTHLY)}
              </MenuItem>
            </Select>
          </FormControl>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            How often to make investments
          </Typography>
        </Box>

        {/* Symbols */}
        <Box sx={{ mb: 2 }}>
          <Box display="flex" alignItems="center" mb={1}>
            <Typography variant="subtitle2">
              Symbols (comma-separated)
            </Typography>
            <Tooltip title={TOOLTIPS.portfolio.symbols} arrow>
              <IconButton size="small" sx={{ ml: 1, p: 0.5 }}>
                <HelpOutline sx={{ fontSize: 16, color: 'info.main' }} />
              </IconButton>
            </Tooltip>
          </Box>
          <TextField
            type="text"
            size="small"
            fullWidth
            value={portfolioSettings.symbols || ''}
            onChange={(e) => setPortfolioSettings({
              ...portfolioSettings,
              symbols: e.target.value
            })}
            placeholder="SPY,AAPL,MSFT,GOOGL"
            helperText="Stock symbols to invest in, separated by commas"
          />
        </Box>

        {/* Rebalance Threshold */}
        <Box sx={{ mb: 2 }}>
          <Box display="flex" alignItems="center" mb={1}>
            <Typography variant="subtitle2">
              Rebalance Threshold (%)
            </Typography>
            <Tooltip title={TOOLTIPS.portfolio.rebalanceThreshold} arrow>
              <IconButton size="small" sx={{ ml: 1, p: 0.5 }}>
                <HelpOutline sx={{ fontSize: 16, color: 'warning.main' }} />
              </IconButton>
            </Tooltip>
          </Box>
          <TextField
            type="number"
            size="small"
            fullWidth
            inputProps={{ min: 1, max: 50 }}
            value={portfolioSettings.rebalance_threshold || 5}
            onChange={(e) => setPortfolioSettings({
              ...portfolioSettings,
              rebalance_threshold: parseFloat(e.target.value)
            })}
            helperText="Trigger rebalancing when allocation drifts by this percentage"
          />
        </Box>
      </Box>
    );
  };

  return (
    <Dialog 
      open={isOpen} 
      onClose={onClose}
      maxWidth="md"
      fullWidth
      scroll="paper"
    >
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h5">
            Settings - {strategy.name}
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>

        {loading && (
          <Box display="flex" flexDirection="column" alignItems="center" py={4}>
            <CircularProgress size={40} />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Loading settings...
            </Typography>
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="subtitle2">Error Loading Settings</Typography>
            {error}
          </Alert>
        )}

        {!loading && !error && (
          <>
            {strategyHelpers.isBTCStrategy(strategy) && <BTCSettingsForm />}
            {strategyHelpers.isPortfolioStrategy(strategy) && <PortfolioSettingsForm />}
          </>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} color="inherit">
          Cancel
        </Button>
        <Button 
          onClick={saveSettings} 
          variant="contained" 
          disabled={saving}
          startIcon={saving ? <CircularProgress size={16} /> : null}
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TypedSettingsModal;