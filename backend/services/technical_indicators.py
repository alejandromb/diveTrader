"""
Advanced Technical Indicators Module for DiveTrader

This module provides a comprehensive collection of technical analysis indicators
commonly used in algorithmic trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """
    Collection of advanced technical indicators for trading strategies
    """
    
    @staticmethod
    def sma(prices: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def ema(prices: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return prices.ewm(span=period).mean()
    
    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index (0-100)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def macd(prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, pd.Series]:
        """
        MACD (Moving Average Convergence Divergence)
        Returns: {'macd': Series, 'signal': Series, 'histogram': Series}
        """
        ema_fast = TechnicalIndicators.ema(prices, fast_period)
        ema_slow = TechnicalIndicators.ema(prices, slow_period)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """
        Bollinger Bands
        Returns: {'upper': Series, 'middle': Series, 'lower': Series}
        """
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                  k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """
        Stochastic Oscillator (%K and %D)
        Returns: {'%K': Series, '%D': Series}
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            '%K': k_percent,
            '%D': d_percent
        }
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range - measures volatility"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = pd.DataFrame({
            'high_low': high_low,
            'high_close': high_close,
            'low_close': low_close
        }).max(axis=1)
        
        return true_range.rolling(window=period).mean()
    
    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Williams %R oscillator (-100 to 0)"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
        return williams_r
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, pd.Series]:
        """
        Average Directional Index (ADX) with +DI and -DI
        Returns: {'ADX': Series, '+DI': Series, '-DI': Series}
        """
        # True Range
        tr = TechnicalIndicators.atr(high, low, close, 1)
        
        # Directional Movement
        plus_dm = np.where((high - high.shift(1)) > (low.shift(1) - low), 
                          np.maximum(high - high.shift(1), 0), 0)
        minus_dm = np.where((low.shift(1) - low) > (high - high.shift(1)), 
                           np.maximum(low.shift(1) - low, 0), 0)
        
        plus_dm = pd.Series(plus_dm, index=high.index)
        minus_dm = pd.Series(minus_dm, index=high.index)
        
        # Smoothed values
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / tr.rolling(window=period).mean())
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / tr.rolling(window=period).mean())
        
        # ADX calculation
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return {
            'ADX': adx,
            '+DI': plus_di,
            '-DI': minus_di
        }
    
    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Volume Weighted Average Price"""
        typical_price = (high + low + close) / 3
        return (typical_price * volume).cumsum() / volume.cumsum()
    
    @staticmethod
    def get_trading_signals(df: pd.DataFrame, **params) -> Dict[str, pd.Series]:
        """
        Generate trading signals based on multiple indicators with configurable parameters
        """
        signals = {}
        
        # Default parameters (user configurable)
        rsi_oversold = params.get('rsi_oversold', 30)
        rsi_overbought = params.get('rsi_overbought', 70)
        sma_fast = params.get('sma_fast_period', 20)
        sma_slow = params.get('sma_slow_period', 50)
        stoch_oversold = params.get('stoch_oversold', 20)
        stoch_overbought = params.get('stoch_overbought', 80)
        adx_strong = params.get('adx_strong_threshold', 25)
        
        try:
            # Calculate required indicators if not present
            if 'rsi' not in df.columns:
                df['rsi'] = TechnicalIndicators.rsi(df['close'])
            
            if 'macd' not in df.columns or 'macd_signal' not in df.columns:
                macd_data = TechnicalIndicators.macd(df['close'])
                df['macd'] = macd_data['macd']
                df['macd_signal'] = macd_data['signal']
            
            if f'sma_{sma_fast}' not in df.columns:
                df[f'sma_{sma_fast}'] = TechnicalIndicators.sma(df['close'], sma_fast)
            if f'sma_{sma_slow}' not in df.columns:
                df[f'sma_{sma_slow}'] = TechnicalIndicators.sma(df['close'], sma_slow)
            
            # Generate signals
            signals['rsi_oversold'] = df['rsi'] < rsi_oversold
            signals['rsi_overbought'] = df['rsi'] > rsi_overbought
            signals['macd_bullish'] = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
            signals['sma_bullish'] = df[f'sma_{sma_fast}'] > df[f'sma_{sma_slow}']
            
            # Composite buy signal
            signals['buy_signal'] = signals['rsi_oversold'] & signals['macd_bullish'] & signals['sma_bullish']
            
        except Exception as e:
            logger.error(f"Error generating trading signals: {e}")
        
        return signals