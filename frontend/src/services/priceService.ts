import axios from 'axios';

export interface PriceData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  lastUpdated: string;
}

class PriceService {
  private readonly COINGECKO_BASE = 'https://api.coingecko.com/api/v3';
  // private readonly FINNHUB_BASE = 'https://finnhub.io/api/v1';
  private readonly YAHOO_FINANCE_BASE = 'https://query1.finance.yahoo.com/v8/finance/chart';
  
  // Free tier API key for Finnhub (you can get one at finnhub.io)
  // For demo purposes, we'll use a fallback approach
  
  async getCryptoPrice(coinId: string): Promise<PriceData> {
    try {
      const response = await axios.get(
        `${this.COINGECKO_BASE}/simple/price?ids=${coinId}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true`
      );
      
      const data = response.data[coinId];
      if (!data) throw new Error(`No data for ${coinId}`);
      
      return {
        symbol: coinId === 'bitcoin' ? 'BTC/USD' : coinId.toUpperCase(),
        price: data.usd,
        change: (data.usd * data.usd_24h_change) / 100,
        changePercent: data.usd_24h_change || 0,
        volume: data.usd_24h_vol || 0,
        lastUpdated: new Date().toISOString()
      };
    } catch (error) {
      console.error(`Error fetching crypto price for ${coinId}:`, error);
      throw error;
    }
  }
  
  async getStockPrice(symbol: string): Promise<PriceData> {
    try {
      // Using Yahoo Finance API (free, no API key required)
      const response = await axios.get(
        `${this.YAHOO_FINANCE_BASE}/${symbol}?interval=1d&range=2d`,
        {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
          }
        }
      );
      
      const result = response.data.chart.result[0];
      const meta = result.meta;
      // const quotes = result.indicators.quote[0];
      
      const currentPrice = meta.regularMarketPrice;
      const previousClose = meta.previousClose;
      const change = currentPrice - previousClose;
      const changePercent = (change / previousClose) * 100;
      
      return {
        symbol: symbol,
        price: currentPrice,
        change: change,
        changePercent: changePercent,
        volume: meta.regularMarketVolume || 0,
        lastUpdated: new Date().toISOString()
      };
    } catch (error) {
      console.error(`Error fetching stock price for ${symbol}:`, error);
      // Fallback to realistic mock data
      return this.getMockStockPrice(symbol);
    }
  }
  
  private getMockStockPrice(symbol: string): PriceData {
    const basePrices: Record<string, number> = {
      'AAPL': 185,
      'TSLA': 260,
      'SPY': 460,
      'MSFT': 350,
      'GOOGL': 140,
      'AMZN': 145,
      'NVDA': 900,
      'META': 520
    };
    
    const basePrice = basePrices[symbol] || 100;
    const randomChange = (Math.random() - 0.5) * basePrice * 0.03; // ±3% change
    const currentPrice = basePrice + randomChange;
    const changePercent = (randomChange / basePrice) * 100;
    
    return {
      symbol,
      price: currentPrice,
      change: randomChange,
      changePercent,
      volume: Math.floor(Math.random() * 10000000) + 1000000,
      lastUpdated: new Date().toISOString()
    };
  }
  
  async getPrice(symbol: string): Promise<PriceData> {
    // Determine if it's crypto or stock
    const cryptoMap: Record<string, string> = {
      'BTC/USD': 'bitcoin',
      'BTC': 'bitcoin',
      'ETH/USD': 'ethereum',
      'ETH': 'ethereum',
      'ADA': 'cardano',
      'DOT': 'polkadot'
    };
    
    if (cryptoMap[symbol]) {
      return this.getCryptoPrice(cryptoMap[symbol]);
    } else {
      return this.getStockPrice(symbol);
    }
  }
  
  async getPrices(symbols: string[]): Promise<PriceData[]> {
    const pricePromises = symbols.map(symbol => 
      this.getPrice(symbol).catch(error => {
        console.error(`Failed to fetch price for ${symbol}:`, error);
        return this.getMockStockPrice(symbol);
      })
    );
    
    return Promise.all(pricePromises);
  }
}

export const priceService = new PriceService();