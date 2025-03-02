import React, { useState } from 'react';
import { userLogin, loginData, getUser, userRegister } from '../../../api/user.tsx';
import './AuthModal.css';

interface AuthModalProps {
  onClose: () => void;
  onSuccess: (userData: any) => void;
}

function AuthModal({ onClose, onSuccess }: AuthModalProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState<loginData>({
    username: '',
    email: '',
    password: '',
    profile_picture: ''
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      if (isLogin) {
        const response = await userLogin(formData);
        const userData = await getUser(response.user_id);
        onSuccess(userData);
        onClose();
      } else {
        if (formData.profile_picture === '') {
          formData.profile_picture = "../../assets/user.svg";
        }
        const userData = await userRegister(formData);
        onSuccess(userData);
        onClose();
      }
    } catch (err: any) {
      console.error('Auth error:', err);
      setError(err.message);
    }
  };

  return (
    <div className="auth-modal-overlay">
      <div className="auth-modal">
        <h2>{isLogin ? '登录' : '注册'}</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="用户名"
            value={formData.username}
            onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
            required
          />
          {!isLogin && (
            <input
              type="email"
              placeholder="邮箱"
              value={formData.email}
              onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
              required
            />
          )}
          <input
            type="password"
            placeholder="密码"
            value={formData.password}
            onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
            required
          />
          {!isLogin && (
            <input
              type="text"
              placeholder="头像URL（可选）"
              value={formData.profile_picture}
              onChange={(e) => setFormData(prev => ({ ...prev, profile_picture: e.target.value }))}
            />
          )}
          <button type="submit">
            {isLogin ? '登录' : '注册'}
          </button>
        </form>
        <div className="auth-switch">
          <button onClick={() => setIsLogin(!isLogin)}>
            {isLogin ? '没有账号？去注册' : '已有账号？去登录'}
          </button>
        </div>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
    </div>
  );
}

export default AuthModal; 