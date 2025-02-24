import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Chat from './pages/chat/Chat';
import Home from './pages/home/Home';
import { General } from './pages/general/General.tsx';
import { UserProvider } from './utils/UserContext.tsx';
import { Info } from './pages/info/Info.tsx';

function App() {
  return (
    <UserProvider>
      <Router>
        <div className="app-container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/home" element={<Home />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/repo" element={<General />} />
            <Route path="/repo/:fileId" element={<Info />} />
          </Routes>
        </div>
      </Router>
    </UserProvider>
  );
}

export default App;
