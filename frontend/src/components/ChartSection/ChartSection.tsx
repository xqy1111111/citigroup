import React from "react";
import "./ChartSection.css";

interface ChartSectionProps {
  charts: {
    title: string;
    actions?: {
      label: string;
      isActive?: boolean;
      onClick?: () => void;
    }[];
  }[];
}

export const ChartSection: React.FC<ChartSectionProps> = ({ charts }) => {
  return (
    <div className="charts-section">
      {charts.map((chart, index) => (
        <div key={index} className="chart-card">
          <div className="chart-header">
            <h3>{chart.title}</h3>
            {chart.actions && (
              <div className="chart-actions">
                {chart.actions.map((action, actionIndex) => (
                  <button
                    key={actionIndex}
                    className={`chart-action ${action.isActive ? 'active' : ''}`}
                    onClick={action.onClick}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="chart-content">
            <div className="chart-placeholder">图表区域</div>
          </div>
        </div>
      ))}
    </div>
  );
}; 