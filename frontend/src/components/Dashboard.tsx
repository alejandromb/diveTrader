import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Box, 
  Container, 
  Typography, 
  Grid, 
  Paper, 
  Button, 
  Card, 
  CardContent, 
  CardActions,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  AppBar
} from '@mui/material';
import { 
  Add as AddIcon, 
  Assessment as AssessmentIcon, 
  Sync as SyncIcon, 
  Code as CodeIcon,
  Dashboard as DashboardIcon,
  TrendingUp as TrendingUpIcon,
  AccountBalance as AccountBalanceIcon,
  Security as SecurityIcon
} from '@mui/icons-material';
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
import ManualTradingPanel from './ManualTradingPanel';

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

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`dashboard-tabpanel-${index}`}
      aria-labelledby={`dashboard-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `dashboard-tab-${index}`,
    'aria-controls': `dashboard-tabpanel-${index}`,
  };
}

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
  const [currentTab, setCurrentTab] = useState(0);

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

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading DiveTrader...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ mb: 0 }}>
        <Container maxWidth="xl" sx={{ py: 3 }}>
          <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
            🏊‍♂️ DiveTrader
          </Typography>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Automated Trading Platform
          </Typography>
        </Container>
      </Paper>

      {/* Navigation Tabs */}
      <AppBar position="static" color="default" elevation={0} sx={{ bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
        <Container maxWidth="xl">
          <Tabs 
            value={currentTab} 
            onChange={handleTabChange} 
            aria-label="dashboard tabs"
            variant="scrollable"
            scrollButtons="auto"
            allowScrollButtonsMobile
          >
            <Tab 
              icon={<DashboardIcon />} 
              label="Overview" 
              {...a11yProps(0)} 
              sx={{ minWidth: { xs: 'auto', sm: 160 } }}
            />
            <Tab 
              icon={<TrendingUpIcon />} 
              label="Strategies" 
              {...a11yProps(1)} 
              sx={{ minWidth: { xs: 'auto', sm: 160 } }}
            />
            <Tab 
              icon={<AccountBalanceIcon />} 
              label="Positions & Trades" 
              {...a11yProps(2)} 
              sx={{ minWidth: { xs: 'auto', sm: 160 } }}
            />
            <Tab 
              icon={<SecurityIcon />} 
              label="Risk Management" 
              {...a11yProps(3)} 
              sx={{ minWidth: { xs: 'auto', sm: 160 } }}
            />
          </Tabs>
        </Container>
      </AppBar>

      {/* Tab Content */}
      <Container maxWidth="xl">
        {/* Tab Panel 0: Overview */}
        <TabPanel value={currentTab} index={0}>
          <PriceTicker symbols={activeSymbols} refreshInterval={30000} />
          
          {/* Account Overview */}
          {accountData && (
            <Paper elevation={2} sx={{ mb: 3, p: 3 }}>
              <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                🏦 Account Overview
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={6} sm={3}>
                  <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="caption" color="text.secondary">Portfolio Value</Typography>
                    <Typography variant="h5" fontWeight="bold">${accountData.portfolio_value.toLocaleString()}</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Paper elevation={1} sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'success.contrastText' }}>
                    <Typography variant="caption">💰 Available Cash</Typography>
                    <Typography variant="h5" fontWeight="bold">${accountData.cash.toLocaleString()}</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="caption" color="text.secondary">Equity</Typography>
                    <Typography variant="h5" fontWeight="bold">${accountData.equity.toLocaleString()}</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Paper elevation={1} sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="caption" color="text.secondary">Buying Power</Typography>
                    <Typography variant="h5" fontWeight="bold">${accountData.buying_power.toLocaleString()}</Typography>
                  </Paper>
                </Grid>
              </Grid>
            </Paper>
          )}

          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <AccountInfo accountData={accountData} loading={!accountData} />
            </Grid>
            <Grid item xs={12} md={4}>
              <ManualTradingPanel />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab Panel 1: Strategies */}
        <TabPanel value={currentTab} index={1}>
          {/* Dashboard Controls */}
          <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
            <Box display="flex" gap={2} flexWrap="wrap">
              <Button 
                variant="contained" 
                startIcon={<AddIcon />}
                onClick={() => setShowCreateStrategy(true)}
              >
                Create Strategy
              </Button>
              <Button 
                variant="outlined" 
                startIcon={<AssessmentIcon />}
                onClick={() => setShowBacktest(true)}
                disabled={!selectedStrategy}
              >
                Backtest
              </Button>
              <Button 
                variant="outlined" 
                startIcon={syncing ? <CircularProgress size={20} /> : <SyncIcon />}
                onClick={handleSyncAllCapitals}
                disabled={syncing}
              >
                {syncing ? 'Syncing...' : 'Sync with Alpaca'}
              </Button>
              <Button 
                variant="outlined" 
                startIcon={<CodeIcon />}
                onClick={() => window.open('http://localhost:8000/docs', '_blank')}
              >
                API Docs
              </Button>
            </Box>
          </Paper>

          <Grid container spacing={3}>
            {/* Strategies List */}
            <Grid item xs={12} xl={6}>
              <Paper elevation={2} sx={{ p: 3 }}>
                <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  🎯 Active Trading Strategies
                </Typography>
                <Alert severity="info" sx={{ mb: 2 }}>
                  💡 Strategies use your available cash (${accountData?.cash.toLocaleString() || '0'}) to execute trades automatically.
                </Alert>
                
                {strategies.length === 0 ? (
                  <Box textAlign="center" py={4}>
                    <Typography variant="body1" color="text.secondary">
                      No strategies yet. Create your first strategy!
                    </Typography>
                  </Box>
                ) : (
                  <Box display="flex" flexDirection="column" gap={2}>
                    {strategies.map(strategy => (
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
                    ))}
                  </Box>
                )}
              </Paper>
            </Grid>

            {/* Performance Metrics */}
            <Grid item xs={12} xl={6}>
              <Paper elevation={2} sx={{ p: 3 }}>
                {selectedStrategy ? (
                  <>
                    <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                      📈 Strategy Performance
                    </Typography>
                    <Alert severity="success" sx={{ mb: 3 }}>
                      🎯 Performance based on actual positions and trades for selected strategy
                    </Alert>
                    
                    {(() => {
                      const strategy = strategies.find(s => s.id === selectedStrategy);
                      if (!strategy) return null;
                      
                      // For now, show all positions since we don't have proper strategy-position mapping
                      const actualPnL = positions.reduce((sum, pos) => sum + pos.unrealized_pnl, 0);
                      const totalInvested = positions.reduce((sum, pos) => sum + (pos.quantity * pos.avg_price), 0);
                      const actualROI = totalInvested > 0 ? (actualPnL / totalInvested) * 100 : 0;
                      
                      return (
                        <Grid container spacing={2} sx={{ mb: 3 }}>
                          <Grid item xs={6}>
                            <Card elevation={1}>
                              <CardContent sx={{ textAlign: 'center' }}>
                                <Typography variant="caption" color="text.secondary">Portfolio ROI</Typography>
                                <Typography variant="h6" color={actualROI >= 0 ? 'success.main' : 'error.main'}>
                                  {actualROI.toFixed(2)}%
                                </Typography>
                              </CardContent>
                            </Card>
                          </Grid>
                          <Grid item xs={6}>
                            <Card elevation={1}>
                              <CardContent sx={{ textAlign: 'center' }}>
                                <Typography variant="caption" color="text.secondary">Unrealized P&L</Typography>
                                <Typography variant="h6" color={actualPnL >= 0 ? 'success.main' : 'error.main'}>
                                  ${actualPnL.toFixed(2)}
                                </Typography>
                              </CardContent>
                            </Card>
                          </Grid>
                          <Grid item xs={6}>
                            <Card elevation={1}>
                              <CardContent sx={{ textAlign: 'center' }}>
                                <Typography variant="caption" color="text.secondary">Total Trades</Typography>
                                <Typography variant="h6">{performance?.total_trades || 0}</Typography>
                              </CardContent>
                            </Card>
                          </Grid>
                          <Grid item xs={6}>
                            <Card elevation={1}>
                              <CardContent sx={{ textAlign: 'center' }}>
                                <Typography variant="caption" color="text.secondary">Win Rate</Typography>
                                <Typography variant="h6">{performance?.win_rate?.toFixed(1) || '0.0'}%</Typography>
                              </CardContent>
                            </Card>
                          </Grid>
                        </Grid>
                      );
                    })()}

                    <Card elevation={1}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>Performance Chart</Typography>
                        <PerformanceChart data={chartData} />
                      </CardContent>
                    </Card>
                  </>
                ) : (
                  <Box textAlign="center" py={4}>
                    <Typography variant="body1" color="text.secondary">
                      Select a strategy to view performance
                    </Typography>
                  </Box>
                )}
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab Panel 2: Positions & Trades */}
        <TabPanel value={currentTab} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} xl={6}>
              <PositionsPanel 
                positions={positions} 
                loading={selectedStrategy ? false : true} 
              />
            </Grid>
            <Grid item xs={12} xl={6}>
              <Box display="flex" flexDirection="column" gap={3}>
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
              </Box>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab Panel 3: Risk Management */}
        <TabPanel value={currentTab} index={3}>
          <RiskManagementPanel 
            strategyId={selectedStrategy}
            refreshInterval={30000}
          />
        </TabPanel>
      </Container>

      {/* Modals */}
      {showBacktest && selectedStrategy && (
        <BacktestModal
          strategyId={selectedStrategy}
          strategy={strategies.find(s => s.id === selectedStrategy)}
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

      {selectedTypedStrategy && (
        <TypedSettingsModal
          strategy={selectedTypedStrategy}
          isOpen={showTypedSettings}
          onClose={closeTypedSettings}
          onSettingsUpdated={onTypedSettingsUpdated}
        />
      )}
    </Box>
  );
};

export default Dashboard;