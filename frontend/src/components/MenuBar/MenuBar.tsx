import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUser } from "../../utils/UserContext.tsx";
import AuthModal from "./AuthModal/AuthModal.tsx";
import "./MenuBar.css";

export function MenuBar() {
  const { user, updateUser, resetUser, resetCurrentRepo } = useUser();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    resetUser();
    resetCurrentRepo();
    navigate("/home");
  };

  return (
    <div className="menu-bar">
      <div className="menu-left">
        {/* 左侧留空 */}
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
          onSuccess={updateUser}
        />
      )}
    </div>
  );
}
