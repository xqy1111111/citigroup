import React from "react";
import "./MenuBar.css";

export const MenuBar = () => {
  return (
    <div className="menubar">
      <div className="menu-items">
        <span className="menu-item">文件</span>
        <span className="menu-item">编辑</span>
        <span className="menu-item">选择</span>
        <span className="menu-item">查看</span>
        <span className="menu-item">转到</span>
        <span className="menu-item">运行</span>
      </div>
    </div>
  );
}; 