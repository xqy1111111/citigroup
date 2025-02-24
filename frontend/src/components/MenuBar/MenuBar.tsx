import React, { useState } from "react";
import { Button } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useUser } from "../../utils/UserContext.tsx";
import AuthModal from "./AuthModal/AuthModal.tsx";
import "./MenuBar.css";

export function MenuBar() {
  const { user, currentRepo, updateUser, resetUser, resetCurrentRepo, } = useUser();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const navigate = useNavigate();

  const handleHomeClick = () => {
    resetCurrentRepo();
    navigate("/home");
  };

  const handleChatClick = () => {
    navigate("/chat");
  };

  const handleAuthSuccess = (userData: any) => {
    updateUser(userData);
  };

  const handleLogout = () => {
    resetUser();
  };

  return (
    <div className="menubar" style={{ backgroundColor: "#333333", color: "white" }}>
      <div className="menu-items">
        <div className="menu-item">文件</div>
        <div className="menu-item">编辑</div>
        <div className="menu-item">选择</div>
        <div className="menu-item">查看</div>
        <div className="menu-item">转到</div>
        <div className="menu-item">运行</div>
        <div className="menu-item">终端</div>
        <div className="menu-item">帮助</div>
        <div style={{
          display: 'flex',
          backgroundColor: 'rgb(51,51,51)',
        }}>
          <Button
            variant="contained"
            onClick={handleHomeClick}
            style={{
              height: '30px',
              backgroundColor: 'rgb(51,51,51)',
              color: 'white',
              borderRadius: '5px',
              marginRight: '10px',
            }}
          >
            Home
          </Button>
          {currentRepo.id !== "" ? (
            <Button
              variant="contained"
              onClick={handleChatClick}
              style={{
                height: '30px',
                backgroundColor: 'rgb(51,51,51)',
                color: 'white',
                borderRadius: '5px',
                marginRight: '10px',
              }}
            >
              Chat
            </Button>) : <></>
          }
        </div>
      </div>
      <div className="menu-right">
        {user.id ? (
          <div className="user-info">
            <img
              src={user.profile_picture || "/default-avatar.png"}
              alt="用户头像"
              className="user-avatar"
            />
            <span className="username">{user.username}</span>
            <button onClick={handleLogout} className="logout-button">
              退出
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowAuthModal(true)}
            className="login-button"
          >
            登录/注册
          </button>
        )}
      </div>

      {showAuthModal && (
        <AuthModal
          onClose={() => setShowAuthModal(false)}
          onSuccess={handleAuthSuccess}
        />
      )}
    </div>
  );
}
