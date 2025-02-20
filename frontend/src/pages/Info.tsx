import React from "react";
import { MenuBar } from "../components/MenuBar/MenuBar";
import { NavigationBar } from "../components/NavigationBar/NavigationBar";
import { Sidebar } from "../components/Sidebar/Sidebar";
import "./Info.css";
import { ChartSection } from "../components/ChartSection/ChartSection";
import { TableSection } from "../components/TableSection/TableSection";

export function Info() {
  const tableData = [
    { id: 1, name: "项目 A", status: "运行中", progress: 75, lastUpdate: "2024-03-15" },
    { id: 2, name: "项目 B", status: "已完成", progress: 100, lastUpdate: "2024-03-14" },
    { id: 3, name: "项目 C", status: "暂停", progress: 30, lastUpdate: "2024-03-13" },
    { id: 4, name: "项目 D", status: "运行中", progress: 60, lastUpdate: "2024-03-12" },
    { id: 5, name: "项目 E", status: "已完成", progress: 100, lastUpdate: "2024-03-11" },
  ];

  const tableActions = [
    { label: "刷新" },
    { label: "导出" }
  ];

  const chartConfigs = [
    {
      title: "项目状态分布",
      actions: [
        { label: "饼图", isActive: true },
        { label: "柱状图" }
      ]
    },
    {
      title: "进度趋势",
      actions: [
        { label: "周" },
        { label: "月", isActive: true },
        { label: "年" }
      ]
    }
  ];

  return (
    <div className="container">
      <MenuBar />
      <div className="main-content">
        <NavigationBar />
        <Sidebar />
        <div className="content">
          <div className="content-header">
            <h1>项目详情</h1>
          </div>

          <div className="info-container">
            <TableSection 
              data={tableData}
              title="项目列表"
              actions={tableActions}
            />
            <ChartSection charts={chartConfigs} />
          </div>
        </div>
      </div>
    </div>
  );
} 