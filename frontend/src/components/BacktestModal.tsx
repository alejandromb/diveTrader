import React, { useState } from 'react';
import axios from 'axios';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  IconButton,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress
} from '@mui/material';
import { Close as CloseIcon, Assessment as AssessmentIcon } from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

interface BacktestResult {
  symbol: string;
  period: string;
  initial_capital: number;
  final_capital: number;
  total_return: number;
  total_return_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  max_drawdown: number;
  sharpe_ratio: number;
  // Enhanced data for comprehensive reporting
  investment_frequency?: string;
  investment_amount?: number;
  total_invested?: number;
  symbols?: string[];
  start_date?: string;
  end_date?: string;
  investments?: Investment[];
  portfolio_evolution?: PortfolioEvolution[];
  allocation_history?: Record<string, any>;
  final_holdings?: Record<string, number>;
}

interface Investment {
  investment_date: string;
  total_invested: number;
  shares_purchased: Record<string, number>;
  prices_used: Record<string, number>;
}

interface PortfolioEvolution {
  date: string;
  portfolio_value: number;
  cash: number;
  holdings_value: number;
  total_return: number;
  total_return_pct: number;
}

interface Strategy {
  id: number;
  name: string;
  strategy_type: string;
  is_active: boolean;
  initial_capital: number;
  current_capital: number;
}

interface BacktestModalProps {
  strategyId: number;
  strategy?: Strategy;
  onClose: () => void;
}

const BacktestModal: React.FC<BacktestModalProps> = ({ strategyId, strategy, onClose }) => {
  const [daysBack, setDaysBack] = useState(30);
  const [initialCapital, setInitialCapital] = useState(10000);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);

  const runBacktest = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(`http://localhost:8000/api/strategies/${strategyId}/backtest`, {
        days_back: daysBack,
        initial_capital: initialCapital,
        config: {} // Add any additional config if needed
      });
      
      setResults(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Backtest failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={true} onClose={onClose} maxWidth="lg" fullWidth maxHeight="90vh"
      PaperProps={{ sx: { height: '90vh' } }}>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssessmentIcon />
            <Typography variant="h6">Strategy Backtest</Typography>
          </Box>
          {strategy && (
            <Typography variant="body2" color="text.secondary">
              Testing: <strong>{strategy.name}</strong> ({strategy.strategy_type.replace('_', ' ').toUpperCase()})
            </Typography>
          )}
        </Box>
        <IconButton onClick={onClose}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent>
        {!results ? (
          <Box sx={{ pt: 2 }}>
            {strategy && (
              <Alert severity="info" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  <strong>Strategy:</strong> {strategy.name}<br />
                  <strong>Type:</strong> {strategy.strategy_type.replace('_', ' ').toUpperCase()}<br />
                  <strong>Current Capital:</strong> ${strategy.current_capital?.toLocaleString() || '0'}<br />
                  <strong>Status:</strong> {strategy.is_active ? '✅ Active' : '⏸️ Inactive'}
                </Typography>
              </Alert>
            )}
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Days to Test"
                  type="number"
                  value={daysBack}
                  onChange={(e) => setDaysBack(Number(e.target.value))}
                  inputProps={{ min: 1, max: 365 }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Initial Capital ($)"
                  type="number"
                  value={initialCapital}
                  onChange={(e) => setInitialCapital(Number(e.target.value))}
                  inputProps={{ min: 100, step: 100 }}
                />
              </Grid>
            </Grid>

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </Box>
        ) : (
          <Box sx={{ pt: 2 }}>
            <Alert severity="success" sx={{ mb: 3 }}>
              <Typography variant="h6">🎯 Backtest Results</Typography>
              <Typography variant="body2">
                <strong>Symbol:</strong> {results.symbol} | <strong>Period:</strong> {results.period}
              </Typography>
              <Typography variant="body2">
                <strong>Initial:</strong> ${results.initial_capital.toLocaleString()} → <strong>Final:</strong> ${results.final_capital.toLocaleString()}
              </Typography>
              {results.investment_frequency && (
                <Typography variant="body2">
                  <strong>Strategy:</strong> {results.investment_frequency} investments of ${results.investment_amount?.toLocaleString()} over {results.symbols?.join(', ')}
                </Typography>
              )}
            </Alert>

            {/* Results Navigation Tabs */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
              <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} aria-label="backtest results tabs">
                <Tab label="Overview" />
                <Tab label="Investments" />
                <Tab label="Holdings" />
                <Tab label="Performance" />
              </Tabs>
            </Box>

            {/* Tab Panel 0: Overview */}
            {tabValue === 0 && (
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={4}>
                  <Card elevation={2}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">Total Return</Typography>
                      <Typography 
                        variant="h6" 
                        color={results.total_return >= 0 ? 'success.main' : 'error.main'}
                      >
                        ${results.total_return.toFixed(2)}
                      </Typography>
                      <Typography 
                        variant="body2" 
                        color={results.total_return >= 0 ? 'success.main' : 'error.main'}
                      >
                        ({results.total_return_pct.toFixed(2)}%)
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={4}>
                  <Card elevation={2}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">Total Invested</Typography>
                      <Typography variant="h6">${results.total_invested?.toLocaleString()}</Typography>
                      <Typography variant="body2">
                        {results.total_trades} investment periods
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={4}>
                  <Card elevation={2}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">Win Rate</Typography>
                      <Typography variant="h6">{results.win_rate.toFixed(1)}%</Typography>
                      <Typography variant="body2">
                        W: {results.winning_trades} | L: {results.losing_trades}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={4}>
                  <Card elevation={2}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">Max Drawdown</Typography>
                      <Typography variant="h6" color="error.main">
                        {results.max_drawdown.toFixed(2)}%
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={4}>
                  <Card elevation={2}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">Sharpe Ratio</Typography>
                      <Typography 
                        variant="h6" 
                        color={results.sharpe_ratio >= 1 ? 'success.main' : 'warning.main'}
                      >
                        {results.sharpe_ratio.toFixed(2)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={4}>
                  <Card elevation={2}>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary">Portfolio Assets</Typography>
                      <Typography variant="h6">{results.symbols?.length || 0}</Typography>
                      <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                        {results.symbols?.join(', ')}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            )}

            {/* Tab Panel 1: Investment History */}
            {tabValue === 1 && results.investments && results.investments.length > 0 && (
              <Card elevation={2}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>📈 Investment History</Typography>
                  <TableContainer component={Paper} elevation={0}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell><strong>Date</strong></TableCell>
                          <TableCell align="right"><strong>Amount</strong></TableCell>
                          <TableCell><strong>Purchases</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {results.investments.map((investment, index) => (
                          <TableRow key={index}>
                            <TableCell>
                              {new Date(investment.investment_date).toLocaleDateString()}
                            </TableCell>
                            <TableCell align="right">
                              <Chip 
                                label={`$${investment.total_invested.toFixed(2)}`}
                                color="primary" 
                                size="small"
                              />
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {Object.entries(investment.shares_purchased).map(([symbol, shares]) => (
                                  <Chip
                                    key={symbol}
                                    label={`${symbol}: ${shares.toFixed(4)} @ $${investment.prices_used[symbol]?.toFixed(2)}`}
                                    variant="outlined"
                                    size="small"
                                  />
                                ))}
                              </Box>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            )}

            {/* Tab Panel 2: Final Holdings */}
            {tabValue === 2 && results.final_holdings && (
              <Card elevation={2}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>🏦 Final Portfolio Holdings</Typography>
                  <Grid container spacing={2}>
                    {Object.entries(results.final_holdings).map(([symbol, shares]) => (
                      <Grid item xs={12} sm={6} md={4} key={symbol}>
                        <Card elevation={1}>
                          <CardContent sx={{ textAlign: 'center' }}>
                            <Typography variant="h6" color="primary.main">{symbol}</Typography>
                            <Typography variant="body1">
                              {shares.toFixed(4)} shares
                            </Typography>
                            <LinearProgress 
                              variant="determinate" 
                              value={(shares / Math.max(...Object.values(results.final_holdings))) * 100}
                              sx={{ mt: 1 }}
                            />
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            )}

            {/* Tab Panel 3: Performance Chart */}
            {tabValue === 3 && (
              <Card elevation={2}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>📊 Portfolio Performance Over Time</Typography>
                  
                  {results.portfolio_evolution && results.portfolio_evolution.length > 0 ? (
                    <Box sx={{ width: '100%', height: 400, mt: 2 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart
                          data={results.portfolio_evolution.map(point => ({
                            date: new Date(point.date).toLocaleDateString(),
                            portfolioValue: point.portfolio_value,
                            totalReturn: point.total_return,
                            returnPct: point.total_return_pct,
                            cash: point.cash,
                            holdingsValue: point.holdings_value
                          }))}
                          margin={{
                            top: 20,
                            right: 30,
                            left: 20,
                            bottom: 60,
                          }}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            dataKey="date" 
                            angle={-45}
                            textAnchor="end"
                            height={80}
                            interval={Math.max(1, Math.floor(results.portfolio_evolution.length / 10))}
                          />
                          <YAxis 
                            yAxisId="left"
                            orientation="left"
                            domain={['dataMin - 100', 'dataMax + 100']}
                            tickFormatter={(value) => `$${value.toLocaleString()}`}
                          />
                          <YAxis 
                            yAxisId="right"
                            orientation="right"
                            domain={['dataMin - 1', 'dataMax + 1']}
                            tickFormatter={(value) => `${value.toFixed(1)}%`}
                          />
                          <Tooltip 
                            formatter={(value: number, name: string) => {
                              if (name === 'returnPct') return [`${value.toFixed(2)}%`, 'Return %'];
                              return [`$${value.toLocaleString()}`, name === 'portfolioValue' ? 'Portfolio Value' : 
                                      name === 'cash' ? 'Cash' : 'Holdings Value'];
                            }}
                            labelFormatter={(label) => `Date: ${label}`}
                          />
                          <Legend />
                          <ReferenceLine yAxisId="left" y={results.initial_capital} stroke="#666" strokeDasharray="5 5" />
                          <Line 
                            yAxisId="left"
                            type="monotone" 
                            dataKey="portfolioValue" 
                            stroke="#2196F3" 
                            strokeWidth={3}
                            name="Portfolio Value"
                            dot={false}
                          />
                          <Line 
                            yAxisId="right"
                            type="monotone" 
                            dataKey="returnPct" 
                            stroke="#4CAF50" 
                            strokeWidth={2}
                            name="Return %"
                            dot={false}
                          />
                          <Line 
                            yAxisId="left"
                            type="monotone" 
                            dataKey="cash" 
                            stroke="#FF9800" 
                            strokeWidth={1}
                            strokeDasharray="3 3"
                            name="Cash"
                            dot={false}
                          />
                          <Line 
                            yAxisId="left"
                            type="monotone" 
                            dataKey="holdingsValue" 
                            stroke="#9C27B0" 
                            strokeWidth={1}
                            strokeDasharray="3 3"
                            name="Holdings Value"
                            dot={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                  ) : (
                    <Alert severity="info" sx={{ mt: 2 }}>
                      📈 No portfolio evolution data available for charting.
                    </Alert>
                  )}
                  
                  {results.portfolio_evolution && results.portfolio_evolution.length > 0 && (
                    <Box sx={{ mt: 3 }}>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Chart Legend:</strong>
                      </Typography>
                      <Grid container spacing={2} sx={{ mt: 1 }}>
                        <Grid item xs={12} sm={6} md={3}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Box sx={{ width: 20, height: 3, bgcolor: '#2196F3' }} />
                            <Typography variant="body2">Portfolio Value (Left axis)</Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Box sx={{ width: 20, height: 3, bgcolor: '#4CAF50' }} />
                            <Typography variant="body2">Return % (Right axis)</Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Box sx={{ width: 20, height: 3, bgcolor: '#FF9800', borderTop: '3px dashed #FF9800' }} />
                            <Typography variant="body2">Cash</Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Box sx={{ width: 20, height: 3, bgcolor: '#9C27B0', borderTop: '3px dashed #9C27B0' }} />
                            <Typography variant="body2">Holdings Value</Typography>
                          </Box>
                        </Grid>
                      </Grid>
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          📊 <strong>Data points:</strong> {results.portfolio_evolution.length} portfolio snapshots over {results.period}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          ➖ <strong>Gray dashed line:</strong> Initial capital baseline (${results.initial_capital.toLocaleString()})
                        </Typography>
                      </Box>
                    </Box>
                  )}
                </CardContent>
              </Card>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        {!results ? (
          <>
            <Button onClick={onClose}>Cancel</Button>
            <Button 
              variant="contained" 
              onClick={runBacktest} 
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : <AssessmentIcon />}
            >
              {loading ? 'Running...' : 'Run Backtest'}
            </Button>
          </>
        ) : (
          <>
            <Button onClick={() => setResults(null)} variant="outlined">
              Run Another Test
            </Button>
            <Button onClick={onClose} variant="contained">
              Close
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default BacktestModal;