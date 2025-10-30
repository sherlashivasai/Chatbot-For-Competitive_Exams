import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';

function ChatWindow({ selectedConversation }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const username = localStorage.getItem('username');

  useEffect(() => {
    async function fetchMessages() {
      if (selectedConversation) {
        // In a real app, you would fetch the message history for this thread_id
        // from the backend. For this example, we'll just clear the messages.
        setMessages([]);
      }
    }
    fetchMessages();
  }, [selectedConversation]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input) return;

    const userMessage = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    const thread_id = selectedConversation ? selectedConversation.thread_id : uuidv4();

    // The backend will start sending events as soon as this request is made
    await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input, username, thread_id }),
    });

    const sse = new EventSource(`http://localhost:8000/chat/stream`);
    setMessages((prev) => [...prev, { sender: 'bot', text: '' }]);

    sse.onmessage = (event) => {
      const eventData = JSON.parse(event.data);

      if (eventData.type === 'token') {
        setMessages((prev) => {
          const lastMessage = prev[prev.length - 1];
          return [
            ...prev.slice(0, -1),
            { ...lastMessage, text: lastMessage.text + eventData.data },
          ];
        });
      } else if (eventData.type === 'quiz_json') {
        try {
          const quizData = JSON.parse(eventData.data);
          const formattedQuiz = `Here is your quiz on ${quizData.topic}:\n\n` +
            quizData.questions.map((q, i) =>
              `${i + 1}. ${q.question}\n- ${q.options.join('\n- ')}\n`
            ).join('\n');

          setMessages((prev) => [
            ...prev.slice(0, -1),
            { sender: 'bot', text: formattedQuiz },
          ]);
        } catch (e) {
          console.error("Failed to parse quiz JSON", e);
        }
      } else if (eventData.type === 'stream_end') {
        sse.close();
        setIsLoading(false);
      } else if (eventData.type === 'error') {
        sse.close();
        setIsLoading(false);
      }
    };

    sse.onerror = (err) => {
      sse.close();
      setIsLoading(false);
    };
  };

  return (
    <div style={{ flexGrow: 1, padding: '20px' }}>
      <div style={{ border: '1px solid #ccc', height: '500px', overflowY: 'scroll', padding: '10px' }}>
        {messages.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left', margin: '10px 0' }}>
            <span style={{
              background: msg.sender === 'user' ? '#dcf8c6' : '#f1f0f0',
              padding: '8px 12px',
              borderRadius: '10px',
              whiteSpace: 'pre-wrap'
            }}>
              {msg.text}
            </span>
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} style={{ display: 'flex', marginTop: '10px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading}
          style={{ flexGrow: 1, padding: '10px' }}
          placeholder="Ask for notes, a quiz, or current affairs..."
        />
        <button type="submit" disabled={isLoading} style={{ padding: '10px' }}>
          {isLoading ? 'Thinking...' : 'Send'}
        </button>
      </form>
    </div>
  );
}

export default ChatWindow;
