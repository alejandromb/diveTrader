import React, { useState, useEffect } from 'react';

interface PriceData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  lastUpdated: string;
}

interface PriceTickerProps {
  symbols: string[];
  refreshInterval?: number;
}

const PriceTicker: React.FC<PriceTickerProps> = ({ symbols, refreshInterval = 30000 }) => {
  const [prices, setPrices] = useState<PriceData[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    if (symbols.length === 0) return;

    const fetchPrices = async () => {
      try {
        // For now, we'll simulate real-time data since Alpaca's real-time requires websockets
        const mockPrices: PriceData[] = symbols.map(symbol => {
          const basePrice = symbol === 'BTC/USD' ? 45000 : 
                           symbol === 'AAPL' ? 175 :
                           symbol === 'TSLA' ? 250 :
                           symbol === 'SPY' ? 450 : 100;
          
          const randomChange = (Math.random() - 0.5) * basePrice * 0.02; // ±2% change
          const currentPrice = basePrice + randomChange;
          const changePercent = (randomChange / basePrice) * 100;
          
          return {
            symbol,
            price: currentPrice,
            change: randomChange,
            changePercent,
            volume: Math.floor(Math.random() * 1000000),
            lastUpdated: new Date().toISOString()
          };
        });
        
        setPrices(mockPrices);
        setLastUpdate(new Date());
        setLoading(false);
      } catch (error) {
        console.error('Error fetching prices:', error);
        setLoading(false);
      }
    };

    fetchPrices();
    const interval = setInterval(fetchPrices, refreshInterval);

    return () => clearInterval(interval);
  }, [symbols, refreshInterval]);

  if (loading) {
    return (
      <div className="price-ticker loading">
        <span>Loading market data...</span>
      </div>
    );
  }

  if (prices.length === 0) {
    return (
      <div className="price-ticker empty">
        <span>No market data available</span>
      </div>
    );
  }

  return (
    <div className="price-ticker">
      <div className="ticker-header">
        <h3>📈 Live Market Data</h3>
        <span className="last-update">
          Updated: {lastUpdate.toLocaleTimeString()}
        </span>
      </div>
      
      <div className="ticker-scroll">
        {prices.map((price) => (
          <div key={price.symbol} className="ticker-item">
            <div className="symbol-section">
              <span className="symbol">{price.symbol}</span>
              <span className="price">${price.price.toFixed(2)}</span>
            </div>
            
            <div className="change-section">
              <span className={`change-amount ${price.change >= 0 ? 'positive' : 'negative'}`}>
                {price.change >= 0 ? '+' : ''}${price.change.toFixed(2)}
              </span>
              <span className={`change-percent ${price.changePercent >= 0 ? 'positive' : 'negative'}`}>
                ({price.changePercent >= 0 ? '+' : ''}{price.changePercent.toFixed(2)}%)
              </span>
            </div>
            
            <div className="volume-section">
              <span className="volume-label">Vol:</span>
              <span className="volume">{(price.volume / 1000).toFixed(0)}K</span>
            </div>
            
            <div className="trend-indicator">
              {price.change >= 0 ? '📈' : '📉'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PriceTicker;