import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Chat from './pages/chat/Chat';
import Home from './pages/home/Home';
import { UserProvider } from './utils/UserContext.tsx';

function App() {
  return (
    <UserProvider>
      <Router>
        <div className="app-container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/home" element={<Home />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/project" element={<h1>项目页面</h1>} />
          </Routes>
        </div>
      </Router>
    </UserProvider>
  );
}

export default App;
