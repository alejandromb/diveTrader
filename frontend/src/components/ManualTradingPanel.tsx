import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Autocomplete,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Search as SearchIcon,
  TrendingUp as BuyIcon,
  TrendingDown as SellIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import axios from 'axios';
import { API_CONFIG } from '../config/constants';

interface StockQuote {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap?: number;
  high: number;
  low: number;
  open: number;
  previousClose: number;
}

// OrderRequest interface removed - using plain objects for API calls

interface Position {
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
}

const API_BASE = API_CONFIG.BASE_URL;

// Popular stocks for quick access
const POPULAR_STOCKS = [
  'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 
  'SPY', 'QQQ', 'IWM', 'GLD', 'SLV', 'ARKK', 'AMD', 'PYPL'
];

const ManualTradingPanel: React.FC = () => {
  const [searchSymbol, setSearchSymbol] = useState('');
  const [selectedStock, setSelectedStock] = useState<StockQuote | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [showOrderDialog, setShowOrderDialog] = useState(false);
  const [orderType, setOrderType] = useState<'buy' | 'sell'>('buy');
  const [orderDetails, setOrderDetails] = useState({
    quantity: 1,
    dollarsAmount: 100, // For fractional share purchases
    buyMode: 'shares' as 'shares' | 'dollars', // Buy by shares or dollar amount
    type: 'market' as 'market' | 'limit',
    timeInForce: 'day' as 'day' | 'gtc',
    limitPrice: 0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dialogError, setDialogError] = useState<string | null>(null); // Error state for dialog
  const [accountData, setAccountData] = useState<any>(null);

  useEffect(() => {
    fetchPositions();
    fetchAccountData();
  }, []);

  const fetchPositions = async () => {
    try {
      const response = await axios.get(`${API_BASE}/trading/positions`);
      setPositions(response.data);
    } catch (error) {
      console.error('Error fetching positions:', error);
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

  const searchStock = async (symbol: string) => {
    if (!symbol.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`${API_BASE}/trading/quote/${symbol.toUpperCase()}`);
      const quote = response.data;
      
      const stockQuote: StockQuote = {
        symbol: quote.symbol,
        price: quote.price,
        change: quote.change,
        changePercent: quote.changePercent,
        volume: quote.volume,
        high: quote.high,
        low: quote.low,
        open: quote.open,
        previousClose: quote.previousClose
      };
      setSelectedStock(stockQuote);
    } catch (error) {
      setError(`Could not find stock: ${symbol}`);
      setSelectedStock(null);
    } finally {
      setLoading(false);
    }
  };

  const openOrderDialog = (type: 'buy' | 'sell') => {
    setOrderType(type);
    setDialogError(null); // Clear any previous dialog errors
    
    // Get current position for this stock (for sell validation)
    const currentPosition = positions.find(p => p.symbol === selectedStock?.symbol);
    const maxSellQuantity = currentPosition ? Math.abs(currentPosition.quantity) : 0;
    
    // For sell orders, validate that user has shares
    if (type === 'sell' && maxSellQuantity === 0) {
      setDialogError(`You don't own any shares of ${selectedStock?.symbol} to sell.`);
    }
    
    setOrderDetails({
      quantity: type === 'sell' ? Math.min(1, maxSellQuantity) : 1,
      dollarsAmount: 100,
      buyMode: 'shares',
      type: 'market',
      timeInForce: 'day',
      limitPrice: selectedStock?.price || 0
    });
    setShowOrderDialog(true);
  };

  const submitOrder = async () => {
    if (!selectedStock) return;

    setLoading(true);
    setDialogError(null); // Clear dialog errors, not main errors
    setSuccess(null);

    // Determine quantity based on buy mode
    let finalQuantity = orderDetails.quantity;
    let notional = undefined;
    
    if (orderType === 'buy' && orderDetails.buyMode === 'dollars') {
      // For dollar-based purchases, use notional value (fractional shares)
      notional = orderDetails.dollarsAmount;
      finalQuantity = undefined; // Don't send quantity for notional orders
    }
    
    const orderRequest = {
      symbol: selectedStock.symbol,
      ...(finalQuantity && { quantity: finalQuantity }),
      ...(notional && { notional: notional }),
      side: orderType,
      type: orderDetails.type,
      time_in_force: orderDetails.timeInForce,
      ...(orderDetails.type === 'limit' && { limit_price: orderDetails.limitPrice })
    };

    try {
      const response = await axios.post(`${API_BASE}/trading/orders`, orderRequest);
      const orderDescription = orderType === 'buy' && orderDetails.buyMode === 'dollars' 
        ? `$${orderDetails.dollarsAmount} of ${selectedStock.symbol}`
        : `${orderDetails.quantity} shares of ${selectedStock.symbol}`;
      setSuccess(`${orderType.toUpperCase()} order submitted for ${orderDescription}`);
      setShowOrderDialog(false);
      fetchPositions(); // Refresh positions
      fetchAccountData(); // Refresh account data
    } catch (error: any) {
      setDialogError(error.response?.data?.detail || `Failed to submit ${orderType} order`);
    } finally {
      setLoading(false);
    }
  };

  const closePosition = async (symbol: string, quantity: number) => {
    if (!window.confirm(`Close entire position in ${symbol}? (${quantity} shares)`)) {
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    const orderRequest = {
      symbol,
      quantity: Math.abs(quantity), // Ensure positive quantity
      side: quantity > 0 ? 'sell' : 'buy', // If long position, sell. If short, buy to cover
      type: 'market',
      time_in_force: 'day'
    };

    try {
      await axios.post(`${API_BASE}/trading/orders`, orderRequest);
      setSuccess(`Closing position: ${Math.abs(quantity)} shares of ${symbol}`);
      fetchPositions();
      fetchAccountData();
    } catch (error: any) {
      setError(error.response?.data?.detail || `Failed to close position in ${symbol}`);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <Paper elevation={2} sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        📈 Manual Trading Suite
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Account Summary */}
      {accountData && (
        <Card elevation={1} sx={{ mb: 3, bgcolor: 'primary.50' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom color="primary.main">
              💰 Available Buying Power
            </Typography>
            <Typography variant="h4" fontWeight="bold">
              {formatCurrency(accountData.buying_power)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Cash: {formatCurrency(accountData.cash)} | Portfolio: {formatCurrency(accountData.portfolio_value)}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Stock Search */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          🔍 Stock Search
        </Typography>
        
        {/* Popular Stocks */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Popular Stocks:
          </Typography>
          <Box display="flex" flexWrap="wrap" gap={1}>
            {POPULAR_STOCKS.map(symbol => (
              <Chip
                key={symbol}
                label={symbol}
                onClick={() => searchStock(symbol)}
                clickable
                size="small"
                variant={selectedStock?.symbol === symbol ? 'filled' : 'outlined'}
                color={selectedStock?.symbol === symbol ? 'primary' : 'default'}
              />
            ))}
          </Box>
        </Box>

        {/* Search Input */}
        <Box display="flex" gap={2} alignItems="center">
          <TextField
            label="Enter Stock Symbol"
            value={searchSymbol}
            onChange={(e) => setSearchSymbol(e.target.value.toUpperCase())}
            onKeyPress={(e) => e.key === 'Enter' && searchStock(searchSymbol)}
            size="small"
            placeholder="AAPL, MSFT, TSLA..."
          />
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={16} /> : <SearchIcon />}
            onClick={() => searchStock(searchSymbol)}
            disabled={loading || !searchSymbol.trim()}
          >
            {loading ? 'Searching...' : 'Search'}
          </Button>
        </Box>
      </Box>

      {/* Stock Quote Display */}
      {selectedStock && (
        <Card elevation={2} sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
              <Box>
                <Typography variant="h4" fontWeight="bold">
                  {selectedStock.symbol}
                </Typography>
                <Typography variant="h5" color={selectedStock.change >= 0 ? 'success.main' : 'error.main'}>
                  {formatCurrency(selectedStock.price)}
                </Typography>
                <Typography variant="body1" color={selectedStock.change >= 0 ? 'success.main' : 'error.main'}>
                  {selectedStock.change >= 0 ? '+' : ''}{selectedStock.change.toFixed(2)} ({formatPercent(selectedStock.changePercent)})
                </Typography>
              </Box>
              
              <IconButton onClick={() => searchStock(selectedStock.symbol)} title="Refresh Quote">
                <RefreshIcon />
              </IconButton>
            </Box>

            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">Open</Typography>
                <Typography variant="body2" fontWeight="medium">{formatCurrency(selectedStock.open)}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">High</Typography>
                <Typography variant="body2" fontWeight="medium">{formatCurrency(selectedStock.high)}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">Low</Typography>
                <Typography variant="body2" fontWeight="medium">{formatCurrency(selectedStock.low)}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">Volume</Typography>
                <Typography variant="body2" fontWeight="medium">{selectedStock.volume.toLocaleString()}</Typography>
              </Grid>
            </Grid>

            {/* Trading Actions */}
            <Box display="flex" gap={2} justifyContent="center">
              <Button
                variant="contained"
                color="success"
                startIcon={<BuyIcon />}
                onClick={() => openOrderDialog('buy')}
                size="large"
              >
                BUY
              </Button>
              <Button
                variant="contained"
                color="error"
                startIcon={<SellIcon />}
                onClick={() => openOrderDialog('sell')}
                size="large"
              >
                SELL
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Current Positions */}
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            📊 Your Positions ({positions.length})
          </Typography>
          <IconButton onClick={fetchPositions} title="Refresh Positions">
            <RefreshIcon />
          </IconButton>
        </Box>

        {positions.length === 0 ? (
          <Card elevation={1}>
            <CardContent sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body1" color="text.secondary">
                No positions found. Start trading to see your holdings here!
              </Typography>
            </CardContent>
          </Card>
        ) : (
          <Grid container spacing={2}>
            {positions.map((position) => (
              <Grid item xs={12} sm={6} md={4} key={position.symbol}>
                <Card elevation={1}>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                      <Typography variant="h6" fontWeight="bold">
                        {position.symbol}
                      </Typography>
                      <Chip
                        label={position.quantity > 0 ? 'LONG' : 'SHORT'}
                        color={position.quantity > 0 ? 'success' : 'error'}
                        size="small"
                      />
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {Math.abs(position.quantity)} shares @ {formatCurrency(position.avg_price)}
                    </Typography>
                    
                    <Box mb={2}>
                      <Typography variant="body1">
                        Market Value: <strong>{formatCurrency(position.market_value)}</strong>
                      </Typography>
                      <Typography 
                        variant="body1" 
                        color={position.unrealized_pnl >= 0 ? 'success.main' : 'error.main'}
                      >
                        P&L: <strong>
                          {formatCurrency(position.unrealized_pnl)} ({formatPercent(position.unrealized_pnl_percent || 0)})
                        </strong>
                      </Typography>
                    </Box>
                    
                    <Button
                      variant="outlined"
                      color="error"
                      fullWidth
                      startIcon={<CloseIcon />}
                      onClick={() => closePosition(position.symbol, position.quantity)}
                      size="small"
                    >
                      Close Position
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>

      {/* Order Dialog */}
      <Dialog open={showOrderDialog} onClose={() => setShowOrderDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            {orderType === 'buy' ? <BuyIcon color="success" /> : <SellIcon color="error" />}
            {orderType.toUpperCase()} {selectedStock?.symbol}
          </Box>
        </DialogTitle>
        
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={3} mt={1}>
            <Box>
              <Typography variant="body1" gutterBottom>
                Current Price: <strong>{formatCurrency(selectedStock?.price || 0)}</strong>
              </Typography>
              
              {/* Available Shares Display for Sell Orders */}
              {orderType === 'sell' && (
                <Typography variant="body2" color="text.secondary">
                  Available shares: <strong>
                    {positions.find(p => p.symbol === selectedStock?.symbol)?.quantity || 0} shares
                  </strong>
                </Typography>
              )}
            </Box>
            
            {/* Dialog Error Display */}
            {dialogError && (
              <Alert severity="error" onClose={() => setDialogError(null)}>
                {dialogError}
              </Alert>
            )}
            
            {/* Buy Mode Selection (only for buy orders) */}
            {orderType === 'buy' && (
              <FormControl fullWidth>
                <InputLabel>Buy Mode</InputLabel>
                <Select
                  value={orderDetails.buyMode}
                  onChange={(e) => setOrderDetails(prev => ({ ...prev, buyMode: e.target.value as 'shares' | 'dollars' }))}
                >
                  <MenuItem value="shares">Buy Shares (whole/fractional)</MenuItem>
                  <MenuItem value="dollars">Buy Dollar Amount (fractional shares)</MenuItem>
                </Select>
              </FormControl>
            )}
            
            {/* Quantity Input */}
            {orderType === 'sell' || orderDetails.buyMode === 'shares' ? (
              <>
                <TextField
                  label={orderType === 'sell' ? 'Shares to Sell' : 'Number of Shares'}
                  type="number"
                  value={orderDetails.quantity}
                  onChange={(e) => {
                    const value = parseFloat(e.target.value) || 0;
                    const currentPosition = positions.find(p => p.symbol === selectedStock?.symbol);
                    const maxSell = currentPosition ? Math.abs(currentPosition.quantity) : 0;
                    
                    // For sell orders, validate against available shares
                    if (orderType === 'sell' && value > maxSell) {
                      setDialogError(`Cannot sell ${value} shares. You only own ${maxSell} shares.`);
                      return;
                    } else {
                      setDialogError(null);
                    }
                    
                    setOrderDetails(prev => ({ ...prev, quantity: value }));
                  }}
                  inputProps={{ 
                    step: orderType === 'buy' ? 0.001 : 1, // Allow fractional for buy
                    min: orderType === 'buy' ? 0.001 : 1,
                    max: orderType === 'sell' ? positions.find(p => p.symbol === selectedStock?.symbol)?.quantity || 0 : undefined
                  }}
                  fullWidth
                  helperText={
                    orderType === 'sell' 
                      ? `Available: ${positions.find(p => p.symbol === selectedStock?.symbol)?.quantity || 0} shares`
                      : 'Supports fractional shares (e.g., 0.5 shares)'
                  }
                />
              </>
            ) : (
              <TextField
                label="Dollar Amount"
                type="number"
                value={orderDetails.dollarsAmount}
                onChange={(e) => setOrderDetails(prev => ({ ...prev, dollarsAmount: parseFloat(e.target.value) || 0 }))}
                inputProps={{ step: 1, min: 1, max: accountData?.buying_power || 10000 }}
                fullWidth
                helperText={`Available buying power: ${formatCurrency(accountData?.buying_power || 0)}`}
              />
            )}
            
            <FormControl fullWidth>
              <InputLabel>Order Type</InputLabel>
              <Select
                value={orderDetails.type}
                onChange={(e) => setOrderDetails(prev => ({ ...prev, type: e.target.value as 'market' | 'limit' }))}
              >
                <MenuItem value="market">Market Order</MenuItem>
                <MenuItem value="limit">Limit Order</MenuItem>
              </Select>
            </FormControl>
            
            {orderDetails.type === 'limit' && (
              <TextField
                label="Limit Price"
                type="number"
                value={orderDetails.limitPrice}
                onChange={(e) => setOrderDetails(prev => ({ ...prev, limitPrice: parseFloat(e.target.value) || 0 }))}
                inputProps={{ step: 0.01, min: 0 }}
                fullWidth
              />
            )}
            
            <FormControl fullWidth>
              <InputLabel>Time in Force</InputLabel>
              <Select
                value={orderDetails.timeInForce}
                onChange={(e) => setOrderDetails(prev => ({ ...prev, timeInForce: e.target.value as 'day' | 'gtc' }))}
              >
                <MenuItem value="day">Day</MenuItem>
                <MenuItem value="gtc">Good Till Canceled</MenuItem>
              </Select>
            </FormControl>
            
            <Alert severity="info">
              <Typography variant="body2">
                <strong>
                  Estimated Total: {
                    orderType === 'buy' && orderDetails.buyMode === 'dollars'
                      ? formatCurrency(orderDetails.dollarsAmount)
                      : formatCurrency((orderDetails.type === 'market' ? selectedStock?.price || 0 : orderDetails.limitPrice) * orderDetails.quantity)
                  }
                </strong>
              </Typography>
              <Typography variant="caption" display="block">
                {orderDetails.type === 'market' ? 'Market orders execute immediately at current market price' : 'Limit orders only execute at your specified price or better'}
              </Typography>
            </Alert>
          </Box>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => {
            setShowOrderDialog(false);
            setDialogError(null); // Clear dialog errors when closing
          }}>Cancel</Button>
          <Button
            variant="contained"
            color={orderType === 'buy' ? 'success' : 'error'}
            onClick={submitOrder}
            disabled={loading || !!dialogError}
            startIcon={loading ? <CircularProgress size={16} /> : null}
          >
            {loading ? 'Submitting...' : `${orderType.toUpperCase()} ${
              orderType === 'buy' && orderDetails.buyMode === 'dollars' 
                ? `$${orderDetails.dollarsAmount}` 
                : `${orderDetails.quantity} Shares`
            }`}
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default ManualTradingPanel;