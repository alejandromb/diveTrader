/**
 * Tooltip configurations for strategy settings
 * Centralized for easy maintenance and future i18n support
 */

export const TOOLTIPS = {
  // BTC Scalping Strategy Tooltips
  btc: {
    maxPositions: "How many Bitcoin positions this strategy can hold at the same time. More positions = more risk but more opportunities.",
    positionSize: "How much Bitcoin to buy in each trade. 0.001 BTC ≈ $100-120. Larger positions = higher profits but more risk per trade.",
    takeProfit: "Sell when Bitcoin price rises by this percentage. 0.002 = 0.2% profit. Lower values = quicker profits but smaller gains.",
    stopLoss: "Sell when Bitcoin price falls by this percentage to limit losses. 0.001 = 0.1% loss. Important for risk management!",
    shortMA: "Short-term moving average period in minutes. Shorter periods = more sensitive to price changes.",
    longMA: "Long-term moving average period in minutes. Longer periods = smoother trend detection.",
    rsiOversold: "RSI level below which Bitcoin is considered oversold (good time to buy). Lower values = fewer but stronger buy signals.",
    rsiOverbought: "RSI level above which Bitcoin is considered overbought (good time to sell). Higher values = fewer but stronger sell signals.",
    paperTrading: "Practice mode - no real money involved. Turn OFF only when you're confident the strategy works!"
  },

  // Portfolio Distributor Strategy Tooltips  
  portfolio: {
    totalBudget: "Total amount this strategy can invest across all stocks. Should not exceed your available cash balance.",
    maxPositionSize: "Maximum amount to invest in any single stock. Helps diversify risk - don't put all your money in one stock!",
    investmentFrequency: "How often to invest money. Weekly = every 7 days, Monthly = once per month. More frequent = better dollar-cost averaging.",
    symbols: "Stock symbols to invest in, separated by commas. Example: AAPL,MSFT,GOOGL,TSLA",
    rebalanceThreshold: "Rebalance portfolio when allocation drifts by this percentage. Lower values = more frequent rebalancing.",
    minCashReserve: "Minimum cash to keep available for emergencies and opportunities. Don't invest 100% of your money!"
  },

  // General tooltips
  general: {
    checkInterval: "How often (in seconds) to check for trading opportunities. Lower values = more frequent checks but higher CPU usage."
  }
} as const;

// Type for tooltip keys to ensure type safety
export type TooltipKey = keyof typeof TOOLTIPS.btc | keyof typeof TOOLTIPS.portfolio | keyof typeof TOOLTIPS.general;