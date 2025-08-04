# Configuration Constants for DiveTrader Backend
# TODO: Move these to environment variables or database configuration

# Default Portfolio Configurations
DEFAULT_PORTFOLIO_SYMBOLS = ['SPY', 'NVDA', 'V', 'JNJ', 'UNH', 'PG', 'JPM', 'MSFT']
DEFAULT_PORTFOLIO_WEIGHTS = {
    'SPY': 20.0,
    'NVDA': 15.0,
    'V': 12.5,
    'JNJ': 12.5,
    'UNH': 12.5,
    'PG': 10.0,
    'JPM': 10.0,
    'MSFT': 7.5
}

# Trading Parameters
DEFAULT_BTC_SCALPING_CONFIG = {
    "position_size": 0.001,  # BTC amount per trade
    "take_profit_pct": 0.002,  # 0.2%
    "stop_loss_pct": 0.001,   # 0.1%
    "lookback_periods": 10,
    "short_ma_periods": 3,
    "long_ma_periods": 5,
    "min_volume": 1000,
    "max_positions": 1,
    "ai_confidence_threshold": 0.6,
    "fallback_volume": 10000
}

# Risk Management Defaults
DEFAULT_RISK_LIMITS = {
    "max_portfolio_risk": 25.0,
    "max_daily_loss": 5.0,
    "max_drawdown": 15.0,
    "max_position_size": 10.0,
    "max_correlation_exposure": 40.0,
    "min_cash_reserve": 10.0,
    "max_leverage": 1.0,
    "position_concentration_limit": 5
}

# Price Fallbacks (TODO: Make these dynamic/API-driven)
FALLBACK_PRICES = {
    'BTC/USD': 75000.0,
    'BTCUSD': 75000.0,
    'AAPL': 185.0,
    'TSLA': 260.0,
    'SPY': 460.0,
    'MSFT': 350.0,
    'NVDA': 140.0,
    'V': 280.0,
    'JNJ': 160.0,
    'UNH': 520.0,
    'PG': 165.0,
    'JPM': 210.0
}

# Investment Defaults
DEFAULT_INITIAL_CAPITAL = 10000
DEFAULT_INVESTMENT_AMOUNT = 1000
DEFAULT_INVESTMENT_FREQUENCY = 'weekly'
DEFAULT_REBALANCE_THRESHOLD = 5.0

# Portfolio Templates
PORTFOLIO_TEMPLATES = {
    "diversified_growth": {
        "name": "Diversified Growth",
        "symbols": DEFAULT_PORTFOLIO_SYMBOLS,
        "weights": DEFAULT_PORTFOLIO_WEIGHTS,
        "description": "Balanced portfolio across sectors with growth focus"
    },
    "conservative": {
        "name": "Conservative",
        "symbols": ['SPY', 'VTI', 'AAPL', 'MSFT'],
        "weights": {'SPY': 40.0, 'VTI': 30.0, 'AAPL': 15.0, 'MSFT': 15.0},
        "description": "Conservative growth with broad market exposure"
    },
    "tech_heavy": {
        "name": "Tech Heavy",
        "symbols": ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA'],
        "weights": {'AAPL': 30.0, 'MSFT': 25.0, 'GOOGL': 20.0, 'NVDA': 15.0, 'TSLA': 10.0},
        "description": "Technology-focused growth portfolio"
    }
}