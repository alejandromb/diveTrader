/**
 * Type-safe API client for DiveTrader v2 endpoints
 * Uses SQLModel-generated schemas for full type safety
 */

import {
  StrategyType,
  InvestmentFrequency
} from '../types/api';
import type {
  Strategy,
  BTCScalpingSettings,
  PortfolioDistributorSettings,
  StrategyListResponse,
  StrategyResponse,
  BTCSettingsResponse,
  PortfolioSettingsResponse
} from '../types/api';

const API_BASE_URL = 'http://localhost:8000/api/v2';

/**
 * Type-safe HTTP client with error handling
 */
class ApiV2Client {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error ${response.status}: ${error}`);
    }

    return response.json();
  }

  // Strategy Management
  async getStrategies(): Promise<Strategy[]> {
    return this.request<Strategy[]>('/strategies/');
  }

  async getStrategy(id: number): Promise<Strategy> {
    return this.request<Strategy>(`/strategies/${id}`);
  }

  async startStrategy(id: number): Promise<{ message: string; is_running: boolean }> {
    return this.request(`/strategies/${id}/start`, { method: 'POST' });
  }

  async stopStrategy(id: number): Promise<{ message: string; is_running: boolean }> {
    return this.request(`/strategies/${id}/stop`, { method: 'POST' });
  }

  async getStrategyStatus(id: number): Promise<any> {
    return this.request(`/strategies/${id}/status`);
  }

  // BTC Scalping Settings
  async getBTCSettings(strategyId: number): Promise<BTCScalpingSettings> {
    return this.request<BTCScalpingSettings>(`/strategies/${strategyId}/btc-settings`);
  }

  async updateBTCSettings(
    strategyId: number,
    settings: Partial<BTCScalpingSettings>
  ): Promise<BTCScalpingSettings> {
    return this.request<BTCScalpingSettings>(`/strategies/${strategyId}/btc-settings`, {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Portfolio Distributor Settings
  async getPortfolioSettings(strategyId: number): Promise<PortfolioDistributorSettings> {
    return this.request<PortfolioDistributorSettings>(`/strategies/${strategyId}/portfolio-settings`);
  }

  async updatePortfolioSettings(
    strategyId: number,
    settings: Partial<PortfolioDistributorSettings>
  ): Promise<PortfolioDistributorSettings> {
    return this.request<PortfolioDistributorSettings>(`/strategies/${strategyId}/portfolio-settings`, {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Enums and Schemas
  async getStrategyTypes(): Promise<Array<{ value: string; name: string }>> {
    return this.request('/strategies/enums/strategy-types');
  }

  async getInvestmentFrequencies(): Promise<Array<{ value: string; name: string }>> {
    return this.request('/strategies/enums/investment-frequencies');
  }

  async getBTCSettingsSchema(): Promise<any> {
    return this.request('/strategies/schema/btc-settings');
  }

  async getPortfolioSettingsSchema(): Promise<any> {
    return this.request('/strategies/schema/portfolio-settings');
  }

  // Account Sync
  async syncStrategyCapital(strategyId: number): Promise<any> {
    return this.request(`/strategies/${strategyId}/sync-capital`, { method: 'POST' });
  }

  async syncAllStrategiesCapital(): Promise<any> {
    return this.request('/strategies/sync-all-capitals', { method: 'POST' });
  }
}

// Export singleton instance
export const apiV2 = new ApiV2Client();

// Export types for convenience
export type {
  Strategy,
  StrategyType,
  InvestmentFrequency,
  BTCScalpingSettings,
  PortfolioDistributorSettings
};

// Helper functions
export const strategyHelpers = {
  /**
   * Check if a strategy is a BTC scalping strategy
   */
  isBTCStrategy(strategy: Strategy): boolean {
    return strategy.strategy_type === StrategyType.BTC_SCALPING;
  },

  /**
   * Check if a strategy is a portfolio distributor strategy
   */
  isPortfolioStrategy(strategy: Strategy): boolean {
    return strategy.strategy_type === StrategyType.PORTFOLIO_DISTRIBUTOR;
  },

  /**
   * Format strategy type for display
   */
  formatStrategyType(type: StrategyType): string {
    switch (type) {
      case StrategyType.BTC_SCALPING:
        return 'BTC Scalping';
      case StrategyType.PORTFOLIO_DISTRIBUTOR:
        return 'Portfolio Distributor';
      default:
        return type;
    }
  },

  /**
   * Format investment frequency for display
   */
  formatInvestmentFrequency(frequency: InvestmentFrequency): string {
    switch (frequency) {
      case InvestmentFrequency.DAILY:
        return 'Daily';
      case InvestmentFrequency.WEEKLY:
        return 'Weekly';
      case InvestmentFrequency.BIWEEKLY:
        return 'Bi-weekly';
      case InvestmentFrequency.MONTHLY:
        return 'Monthly';
      default:
        return frequency;
    }
  }
};

export default apiV2;