import React from "react";
import { MenuBar } from "../../components/MenuBar/MenuBar";
import { NavigationBar } from "../../components/NavigationBar/NavigationBar";
import { Sidebar } from "../../components/Sidebar/Sidebar";
import "./General.css";

export function General() {
  return (
    <div className="container">
      <MenuBar />
      <div className="main-content">
        <NavigationBar />
        <Sidebar />
        <div className="content">
          <div className="content-header">
            <h1>仪表盘概览</h1>
          </div>

          <div className="stats-container">
            <div className="stat-card">
              <div className="stat-title">总用户数</div>
              <div className="stat-value">12,345</div>
              <div className="stat-change positive">+12.3%</div>
            </div>
            <div className="stat-card">
              <div className="stat-title">活跃用户</div>
              <div className="stat-value">5,678</div>
              <div className="stat-change positive">+8.7%</div>
            </div>
            <div className="stat-card">
              <div className="stat-title">总收入</div>
              <div className="stat-value">¥89,012</div>
              <div className="stat-change negative">-2.4%</div>
            </div>
            <div className="stat-card">
              <div className="stat-title">转化率</div>
              <div className="stat-value">23.4%</div>
              <div className="stat-change positive">+5.2%</div>
            </div>
          </div>

          <div className="charts-container">
            <div className="chart-card">
              <div className="chart-header">
                <h3>用户增长趋势</h3>
                <div className="chart-actions">
                  <button className="chart-action">周</button>
                  <button className="chart-action active">月</button>
                  <button className="chart-action">年</button>
                </div>
              </div>
              <div className="chart-content">
                {/* 这里放置实际的图表组件 */}
                <div className="chart-placeholder">图表区域</div>
              </div>
            </div>

            <div className="chart-card">
              <div className="chart-header">
                <h3>收入分析</h3>
                <div className="chart-actions">
                  <button className="chart-action">导出</button>
                </div>
              </div>
              <div className="chart-content">
                <div className="chart-placeholder">图表区域</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
