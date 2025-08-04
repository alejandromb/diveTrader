// Configuration Constants for DiveTrader Frontend
// TODO: Move to environment variables and/or API configuration

// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3
};

// Default Portfolio Configurations
export const DEFAULT_PORTFOLIO = {
  SYMBOLS: ['SPY', 'NVDA', 'V', 'JNJ', 'UNH', 'PG', 'JPM', 'MSFT'],
  SYMBOLS_TEXT: 'SPY,NVDA,V,JNJ,UNH,PG,JPM,MSFT',
  WEIGHTS_TEXT: '20,15,12.5,12.5,12.5,10,10,7.5',
  WEIGHTS: {
    'SPY': 20.0,
    'NVDA': 15.0,
    'V': 12.5,
    'JNJ': 12.5,
    'UNH': 12.5,
    'PG': 10.0,
    'JPM': 10.0,
    'MSFT': 7.5
  }
};

// Default Strategy Parameters
export const DEFAULT_STRATEGY_CONFIG = {
  BTC_SCALPING: {
    risk_per_trade: 2,
    max_daily_trades: 10,
    stop_loss_percent: 2,
    take_profit_percent: 3
  },
  PORTFOLIO_DISTRIBUTOR: {
    investment_frequency: 'weekly' as const,
    investment_amount: 1000,
    rebalance_threshold: 5
  }
};

// UI Configuration
export const UI_CONFIG = {
  REFRESH_INTERVALS: {
    DASHBOARD: 30000,
    PRICE_TICKER: 30000,
    RISK_PANEL: 30000
  },
  PAGINATION: {
    DEFAULT_PAGE_SIZE: 20,
    MAX_PAGE_SIZE: 100
  }
};

// Investment Defaults
export const INVESTMENT_DEFAULTS = {
  INITIAL_CAPITAL: 10000,
  MIN_INVESTMENT: 100,
  MIN_INVESTMENT_STEP: 100
};

// Fallback Prices (TODO: Remove when API is reliable)
export const FALLBACK_PRICES: Record<string, number> = {
  'AAPL': 185,
  'TSLA': 260,
  'SPY': 460,
  'MSFT': 350,
  'GOOGL': 140,
  'AMZN': 145,
  'NVDA': 140,
  'V': 280,
  'JNJ': 160,
  'UNH': 520,
  'PG': 165,
  'JPM': 210
};

// Portfolio Templates
export const PORTFOLIO_TEMPLATES = {
  diversified_growth: {
    name: "Diversified Growth",
    symbols: DEFAULT_PORTFOLIO.SYMBOLS,
    symbolsText: DEFAULT_PORTFOLIO.SYMBOLS_TEXT,
    weightsText: DEFAULT_PORTFOLIO.WEIGHTS_TEXT,
    description: "Balanced portfolio across sectors with growth focus"
  },
  conservative: {
    name: "Conservative",
    symbols: ['SPY', 'VTI', 'AAPL', 'MSFT'],
    symbolsText: 'SPY,VTI,AAPL,MSFT',
    weightsText: '40,30,15,15',
    description: "Conservative growth with broad market exposure"
  },
  tech_heavy: {
    name: "Tech Heavy", 
    symbols: ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA'],
    symbolsText: 'AAPL,MSFT,GOOGL,NVDA,TSLA',
    weightsText: '30,25,20,15,10',
    description: "Technology-focused growth portfolio"
  }
};

// External API Configuration (TODO: Move to environment variables)
export const EXTERNAL_APIS = {
  COINGECKO: {
    BASE_URL: 'https://api.coingecko.com/api/v3',
    TIMEOUT: 10000
  },
  YAHOO_FINANCE: {
    BASE_URL: 'https://query1.finance.yahoo.com/v8/finance/chart',
    TIMEOUT: 10000
  }
};