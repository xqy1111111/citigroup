import React from "react";
import "./Sidebar.css";

export const Sidebar = () => {
  return (
    <div className="sidebar">
      <div className="sidebar-title">资源管理器</div>
      <div className="sidebar-section">
        <div className="section-header">
          <span className="section-arrow">▼</span>
          <span className="section-name">打开的编辑器</span>
        </div>
        <div className="section-content">
          <div className="file-entry active">
            <i className="icon-file-code"></i>
            <span>index.tsx</span>
          </div>
          <div className="file-entry">
            <i className="icon-file-code"></i>
            <span>General.tsx</span>
          </div>
        </div>
      </div>
      
      <div className="sidebar-section">
        <div className="section-header">
          <span className="section-arrow">▼</span>
          <span className="section-name">my-project</span>
        </div>
        <div className="section-content">
          <div className="folder-entry">
            <span className="folder-arrow">▶</span>
            <i className="icon-folder"></i>
            <span>src</span>
          </div>
          <div className="folder-entry open">
            <span className="folder-arrow">▼</span>
            <i className="icon-folder-open"></i>
            <span>components</span>
          </div>
          <div className="file-entry indent">
            <i className="icon-file-code"></i>
            <span>Button.tsx</span>
          </div>
          <div className="file-entry indent">
            <i className="icon-file-code"></i>
            <span>Card.tsx</span>
          </div>
        </div>
      </div>
    </div>
  );
}; 