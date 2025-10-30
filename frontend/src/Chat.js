import React, { useState, useEffect } from 'react';

// A unique ID for the chat thread (in a real app, you'd generate/store this)
const THREAD_ID = "main-user-thread";

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input) return;

    const userMessage = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // This is the new streaming part
    const sse = new EventSource('http://localhost:8000/chat/stream');

    // Add a placeholder message for the bot's response
    setMessages((prev) => [...prev, { sender: 'bot', text: '' }]);

    sse.onopen = () => {
      console.log("SSE connection opened!");
      // Send the request *after* the connection is open
      fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input, thread_id: THREAD_ID }),
      });
    };

    sse.onmessage = (event) => {
      const eventData = JSON.parse(event.data);

      if (eventData.type === 'token') {
        // Append the new token to the last bot message
        setMessages((prev) => {
          const lastMessage = prev[prev.length - 1];
          return [
            ...prev.slice(0, -1),
            { ...lastMessage, text: lastMessage.text + eventData.data },
          ];
        });
      } else if (eventData.type === 'quiz_json') {
        // Handle the special quiz JSON
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
        console.log("Stream ended");
        sse.close(); // Close the connection
        setIsLoading(false);
      } else if (eventData.type === 'error') {
        console.error("Stream error:", eventData.data);
        sse.close();
        setIsLoading(false);
      }
    };

    sse.onerror = (err) => {
      console.error('EventSource failed:', err);
      sse.close();
      setIsLoading(false);
    };
  };

  return (
    <div style={{ padding: '20px', maxWidth: '700px', margin: 'auto' }}>
      <h1>UPSC/SSC Exam Bot</h1>
      <div style={{ border: '1px solid #ccc', height: '500px', overflowY: 'scroll', padding: '10px' }}>
        {messages.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left', margin: '10px 0' }}>
            <span style={{ 
              background: msg.sender === 'user' ? '#dcf8c6' : '#f1f0f0', 
              padding: '8px 12px', 
              borderRadius: '10px',
              whiteSpace: 'pre-wrap' // This preserves newlines
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

export default Chat;