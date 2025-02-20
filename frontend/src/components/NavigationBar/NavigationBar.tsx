import React from "react";
import "./NavigationBar.css";

export const NavigationBar = () => {
  return (
    <div className="navigation-bar">
      <div className="nav-items">
        <div className="nav-item active">
          <i className="icon-files"></i>
        </div>
        <div className="nav-item">
          <i className="icon-search"></i>
        </div>
        <div className="nav-item">
          <i className="icon-git"></i>
        </div>
        <div className="nav-item">
          <i className="icon-debug"></i>
        </div>
        <div className="nav-item">
          <i className="icon-extensions"></i>
        </div>
      </div>
    </div>
  );
}; 