import React from 'react';

function Sidebar({ conversations, setSelectedConversation }) {
  return (
    <div style={{ width: '200px', borderRight: '1px solid #ccc', padding: '10px' }}>
      <button onClick={() => setSelectedConversation(null)} style={{ width: '100%', marginBottom: '10px' }}>
        + New Chat
      </button>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {conversations.map((convo) => (
          <li
            key={convo.thread_id}
            onClick={() => setSelectedConversation(convo)}
            style={{ padding: '8px', cursor: 'pointer', borderBottom: '1px solid #eee' }}
          >
            {convo.title}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Sidebar;
