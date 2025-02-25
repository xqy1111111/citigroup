import React from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../../utils/UserContext";
import "./NavigationBar.css";

export function NavigationBar() {
  const navigate = useNavigate();
  const { resetCurrentRepo } = useUser();

  const handleHomeClick = () => {
    navigate("/home");
    resetCurrentRepo();
  };

  const handleChatClick = () => {
    navigate("/chat");
  };

  return (
    <div className="navigation-bar">
      <div className="nav-buttons">
        <button className="nav-button" onClick={handleHomeClick}>
          <img src="/user.svg" alt="File" className="nav-icon" />
        </button>
        <button className="nav-button" onClick={handleChatClick}>
          <img src="/robot.svg" alt="Chat" className="nav-icon" />
        </button>
      </div>
    </div>
  );
} 