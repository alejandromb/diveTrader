import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Divider
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Settings as SettingsIcon,
  Assignment as LogsIcon,
  MoreVert as MoreIcon,
  Delete as DeleteIcon,
  MonetizationOn as CryptoIcon,
  TrendingUp as TrendingUpIcon
} from '@mui/icons-material';
import type { Strategy, BTCScalpingSettings, PortfolioDistributorSettings } from '../types/api';
import { apiV2 } from '../services/apiV2';

interface StrategyCardProps {
  strategy: Strategy;
  isSelected: boolean;
  onSelect: () => void;
  onStart: () => void;
  onStop: () => void;
  onDelete: () => void;
  onViewLogs?: () => void;
  onViewSettings?: () => void;
}

const StrategyCard: React.FC<StrategyCardProps> = ({
  strategy,
  isSelected,
  onSelect,
  onStart,
  onStop,
  onDelete,
  onViewLogs,
  onViewSettings
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [btcSettings, setBtcSettings] = useState<BTCScalpingSettings | null>(null);
  const [portfolioSettings, setPortfolioSettings] = useState<PortfolioDistributorSettings | null>(null);
  const menuOpen = Boolean(anchorEl);

  // Load strategy settings
  useEffect(() => {
    const loadSettings = async () => {
      try {
        if (strategy.strategy_type === 'btc_scalping') {
          const settings = await apiV2.getBTCSettings(strategy.id);
          setBtcSettings(settings);
        } else if (strategy.strategy_type === 'portfolio_distributor') {
          const settings = await apiV2.getPortfolioSettings(strategy.id);
          setPortfolioSettings(settings);
        }
      } catch (error) {
        console.error('Error loading strategy settings:', error);
        // Set default values on error
        if (strategy.strategy_type === 'btc_scalping') {
          setBtcSettings({
            strategy_id: strategy.id,
            position_size: 0.001,
            max_positions: 5
          });
        } else if (strategy.strategy_type === 'portfolio_distributor') {
          setPortfolioSettings({
            strategy_id: strategy.id,
            investment_amount: 500,
            max_position_size: 200
          });
        }
      }
    };

    loadSettings();
  }, [strategy.id, strategy.strategy_type]);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const getStrategyIcon = (type: string) => {
    switch (type) {
      case 'btc_scalping':
        return '₿';
      case 'portfolio_distributor':
        return '📊';
      default:
        return '🤖';
    }
  };

  const getStrategyStatus = (strategy: Strategy) => {
    if (!strategy.is_active) {
      return {
        text: '🔴 Disabled',
        color: '#757575',
        description: 'Strategy is disabled'
      };
    } else if (strategy.is_running) {
      return {
        text: '🟢 Running',
        color: '#4CAF50',
        description: 'Strategy is active and executing trades'
      };
    } else {
      return {
        text: '🟡 Enabled but Stopped',
        color: '#FF9800',
        description: 'Strategy is enabled but not executing trades'
      };
    }
  };

  return (
    <Card 
      elevation={isSelected ? 4 : 1}
      sx={{ 
        cursor: 'pointer',
        border: isSelected ? 2 : 0,
        borderColor: 'primary.main',
        '&:hover': { elevation: 3 }
      }}
      onClick={onSelect}
    >
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            {strategy.strategy_type === 'btc_scalping' ? <CryptoIcon color="warning" /> : <TrendingUpIcon color="primary" />}
            <Box>
              <Typography variant="h6" component="h3">
                {strategy.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {strategy.strategy_type.replace('_', ' ').toUpperCase()}
              </Typography>
            </Box>
          </Box>
          
          <Chip 
            label={strategy.is_running ? 'Running' : 'Stopped'}
            color={strategy.is_running ? 'success' : 'default'}
            size="small"
            variant={strategy.is_running ? 'filled' : 'outlined'}
          />
        </Box>

        <Box display="flex" flexDirection="column" gap={1}>
          <Box display="flex" justifyContent="space-between">
            <Typography variant="body2" color="text.secondary">💰 Max Budget:</Typography>
            <Typography variant="body2" fontWeight="medium">
              {strategy.strategy_type === 'btc_scalping' && btcSettings ? 
                `${btcSettings.max_positions || 5} positions` :
               strategy.strategy_type === 'portfolio_distributor' && portfolioSettings ? 
                `$${portfolioSettings.investment_amount || 0}` :
               'Loading...'}
            </Typography>
          </Box>
          
          <Box display="flex" justifyContent="space-between">
            <Typography variant="body2" color="text.secondary">💵 Total Invested:</Typography>
            <Typography variant="body2" fontWeight="medium" color="primary.main">
              ${strategy.total_invested?.toFixed(2) || '0.00'}
            </Typography>
          </Box>
          
          <Box display="flex" justifyContent="space-between">
            <Typography variant="body2" color="text.secondary">🎯 Trade Size:</Typography>
            <Typography variant="body2" fontWeight="medium">
              {strategy.strategy_type === 'btc_scalping' && btcSettings ? 
                `${btcSettings.position_size || 0.001} BTC` :
               strategy.strategy_type === 'portfolio_distributor' && portfolioSettings ? 
                `$${Math.max(portfolioSettings.max_position_size || 100, 100)} max` :
               'Loading...'}
            </Typography>
          </Box>
          
          <Box display="flex" justifyContent="space-between">
            <Typography variant="body2" color="text.secondary">📊 Status:</Typography>
            <Typography 
              variant="body2" 
              fontWeight="medium"
              color={strategy.is_running ? 'success.main' : 'text.primary'}
            >
              {strategy.is_running ? 'Active & Trading' : 'Ready to Trade'}
            </Typography>
          </Box>
        </Box>
      </CardContent>

      <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
        <Box display="flex" gap={1}>
          {strategy.is_running ? (
            <Button 
              variant="contained"
              color="error"
              size="small"
              startIcon={<StopIcon />}
              onClick={(e) => {
                e.stopPropagation();
                onStop();
              }}
            >
              Stop
            </Button>
          ) : (
            <Button 
              variant="contained"
              color="success"
              size="small"
              startIcon={<PlayIcon />}
              onClick={(e) => {
                e.stopPropagation();
                onStart();
              }}
              disabled={!strategy.is_active}
              title={!strategy.is_active ? "Strategy must be enabled first" : "Start executing trades"}
            >
              Start
            </Button>
          )}
          
          {onViewLogs && (
            <IconButton 
              size="small"
              color="primary"
              onClick={(e) => {
                e.stopPropagation();
                onViewLogs();
              }}
              title="View Event Logs"
            >
              <LogsIcon />
            </IconButton>
          )}
        </Box>
        
        <IconButton 
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            handleMenuClick(e);
          }}
          title="More Actions"
        >
          <MoreIcon />
        </IconButton>
        
        <Menu
          anchorEl={anchorEl}
          open={menuOpen}
          onClose={handleMenuClose}
          onClick={(e) => e.stopPropagation()}
        >
          {onViewSettings && (
            <MenuItem onClick={(e) => {
              e.stopPropagation();
              handleMenuClose();
              onViewSettings();
            }}>
              <SettingsIcon sx={{ mr: 1 }} />
              Settings
            </MenuItem>
          )}
          
          <Divider />
          
          <MenuItem 
            onClick={(e) => {
              e.stopPropagation();
              handleMenuClose();
              if (window.confirm(`Are you sure you want to delete "${strategy.name}"?`)) {
                onDelete();
              }
            }}
            sx={{ color: 'error.main' }}
          >
            <DeleteIcon sx={{ mr: 1 }} />
            Delete
          </MenuItem>
        </Menu>
      </CardActions>
    </Card>
  );
};

export default StrategyCard;