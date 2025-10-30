import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import Login from './Login';
import Chat from './Chat';

function App() {
  const user = localStorage.getItem('username');

  return (
    <Router>
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/" /> : <Login />} />
        <Route path="/" element={user ? <Chat /> : <Navigate to="/login" />} />
      </Routes>
    </Router>
  );
}

export default App;
