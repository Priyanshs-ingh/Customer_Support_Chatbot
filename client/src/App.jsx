import React, { useState, useRef, useEffect } from 'react';
import './App.css'

function App() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const sendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage = input;
        setInput('');
        setMessages(prev => [...prev, { text: userMessage, isUser: true }]);
        setIsLoading(true);

        try {
            const response = await fetch('http://127.0.0.1:8000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage }),
            });

            const data = await response.json();
            console.log('Server response:', data); // Log the full response

            if (!response.ok) {
                throw new Error(data.error || 'Failed to save chat message');
            }

            if (!data.success) {
                throw new Error(data.message || 'Database operation failed');
            }

            setMessages(prev => [...prev, { 
                text: data.response,
                category: data.category,
                sentiment: data.sentiment,
                isUser: false 
            }]);
        } catch (error) {
            console.error('Error:', error);
            setMessages(prev => [...prev, { 
                text: `Error: ${error.message}. Please try again.`, 
                isUser: false 
            }]);
        }

        setIsLoading(false);
    };

  return (
    <div className="chatbot-main">
    <div className="chatbot-header">
        <h2>Customer Support</h2>
    </div>
    <div className="messages-container">
        {messages.length === 0 && (
            <div className="welcome-message">
                <p>👋 Hi! How can I help you today?</p>
            </div>
        )}
        {messages.map((message, index) => (
            <div 
                key={index} 
                className={`message-wrapper ${message.isUser ? 'user' : 'bot'}`}
            >
                <div className="message">
                    <span className="message-icon">
                        {message.isUser ? '👤' : '🤖'}
                    </span>
                    <div className="message-content">
                        {message.text}
                    </div>
                </div>
            </div>
        ))}
        {isLoading && (
            <div className="message-wrapper bot">
                <div className="message">
                    <span className="message-icon">🤖</span>
                    <div className="message-content typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        )}
        <div ref={messagesEndRef} />
    </div>
    <form onSubmit={sendMessage} className="input-container">
        <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="message-input"
        />
        <button type="submit" className="send-button">
            Send
        </button>
    </form>
</div>
  )
}

export default App
