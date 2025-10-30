import React, { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import ChatWindow from './ChatWindow';

function Chat() {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const username = localStorage.getItem('username');

  useEffect(() => {
    async function fetchConversations() {
      const response = await fetch(`http://localhost:8000/conversations/${username}`);
      const data = await response.json();
      setConversations(data);
    }
    fetchConversations();
  }, [username]);

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar
        conversations={conversations}
        setSelectedConversation={setSelectedConversation}
      />
      <ChatWindow selectedConversation={selectedConversation} />
    </div>
  );
}

export default Chat;
