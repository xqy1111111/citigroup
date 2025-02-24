import React from "react";
import "./TableSection.css";

interface TableData {
  id: number;
  name: string;
  status: string;
  progress: number;
  lastUpdate: string;
}

interface TableSectionProps {
  data: TableData[];
  title: string;
  actions?: {
    label: string;
    onClick?: () => void;
  }[];
}

export const TableSection: React.FC<TableSectionProps> = ({ data, title, actions }) => {
  return (
    <div className="table-section">
      <div className="table-header">
        <h3>{title}</h3>
        {actions && (
          <div className="table-actions">
            {actions.map((action, index) => (
              <button
                key={index}
                className="table-action"
                onClick={action.onClick}
              >
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>项目名称</th>
              <th>状态</th>
              <th>进度</th>
              <th>最后更新</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr key={item.id}>
                <td>{item.id}</td>
                <td>{item.name}</td>
                <td>
                  <span className={`status-badge ${item.status}`}>
                    {item.status}
                  </span>
                </td>
                <td>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{ width: `${item.progress}%` }}
                    ></div>
                  </div>
                </td>
                <td>{item.lastUpdate}</td>
                <td>
                  <button className="row-action">详情</button>
                  <button className="row-action">编辑</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}; 