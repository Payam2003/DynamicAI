import React from 'react';

function ChatBox({ messages }) {
    return (
        <div className="chat-box h-100 overflow-y-auto mb-4 p-4 border border-gray-300 rounded">
            {messages.map((msg, index) => (
                <div key={index} className={`p-2 mb-2 rounded-lg ${msg.sender === "You" ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-900"}`}>
                    <strong>{msg.sender}:</strong> {msg.text}
                </div>
            ))}
        </div>
    );
}

export default ChatBox;