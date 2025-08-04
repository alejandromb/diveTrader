import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartData {
  date: string;
  total_value: number;
  roi_percentage: number;
  cumulative_pnl: number;
}

interface PerformanceChartProps {
  data: ChartData[];
}

const PerformanceChart: React.FC<PerformanceChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">
        <p>No performance data available yet.</p>
        <p>Start trading to see your performance chart!</p>
      </div>
    );
  }

  // Format data for chart
  const chartData = data.map(item => ({
    date: new Date(item.date).toLocaleDateString(),
    portfolio: item.total_value,
    roi: item.roi_percentage,
    pnl: item.cumulative_pnl
  }));

  return (
    <div className="performance-chart">
      <div className="chart-tabs">
        <button className="tab active">Portfolio Value</button>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            fontSize={12}
            tick={{ fill: '#666' }}
          />
          <YAxis 
            fontSize={12}
            tick={{ fill: '#666' }}
            tickFormatter={(value) => `$${value.toLocaleString()}`}
          />
          <Tooltip 
            formatter={(value: number, name: string) => [
              name === 'portfolio' ? `$${value.toLocaleString()}` : `${value.toFixed(2)}%`,
              name === 'portfolio' ? 'Portfolio Value' : 'ROI'
            ]}
            labelFormatter={(label) => `Date: ${label}`}
          />
          <Line 
            type="monotone" 
            dataKey="portfolio" 
            stroke="#2196F3" 
            strokeWidth={2}
            dot={{ r: 3, fill: '#2196F3' }}
            activeDot={{ r: 5, fill: '#2196F3' }}
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="chart-summary">
        <div className="summary-item">
          <span className="label">Period:</span>
          <span className="value">{data.length} days</span>
        </div>
        <div className="summary-item">
          <span className="label">Latest ROI:</span>
          <span className={`value ${data[data.length - 1]?.roi_percentage >= 0 ? 'positive' : 'negative'}`}>
            {data[data.length - 1]?.roi_percentage.toFixed(2)}%
          </span>
        </div>
        <div className="summary-item">
          <span className="label">Total P&L:</span>
          <span className={`value ${data[data.length - 1]?.cumulative_pnl >= 0 ? 'positive' : 'negative'}`}>
            ${data[data.length - 1]?.cumulative_pnl.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default PerformanceChart;