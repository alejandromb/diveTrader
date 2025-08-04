import React from 'react';

interface AccountInfoProps {
  accountData: {
    equity: number;
    cash: number;
    buying_power: number;
    portfolio_value: number;
    day_trade_count: number;
  } | null;
  loading: boolean;
}

const AccountInfo: React.FC<AccountInfoProps> = ({ accountData, loading }) => {
  if (loading) {
    return (
      <div className="account-panel">
        <h2>Account Info</h2>
        <div className="loading-spinner">Loading account data...</div>
      </div>
    );
  }

  if (!accountData) {
    return (
      <div className="account-panel">
        <h2>Account Info</h2>
        <div className="error-state">Failed to load account data</div>
      </div>
    );
  }

  return (
    <div className="account-panel">
      <h2>💰 Account Overview</h2>
      <div className="account-metrics">
        <div className="account-metric-card primary">
          <h3>Portfolio Value</h3>
          <p className="value large">${accountData.portfolio_value.toFixed(2)}</p>
        </div>
        
        <div className="account-metric-card">
          <h3>Equity</h3>
          <p className="value">${accountData.equity.toFixed(2)}</p>
        </div>
        
        <div className="account-metric-card">
          <h3>Cash</h3>
          <p className="value">${accountData.cash.toFixed(2)}</p>
        </div>
        
        <div className="account-metric-card">
          <h3>Buying Power</h3>
          <p className="value">${accountData.buying_power.toFixed(2)}</p>
        </div>
        
        <div className="account-metric-card">
          <h3>Day Trades Used</h3>
          <p className="value">{accountData.day_trade_count}/3</p>
          <div className="day-trade-bar">
            <div 
              className="day-trade-fill" 
              style={{ width: `${(accountData.day_trade_count / 3) * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AccountInfo;