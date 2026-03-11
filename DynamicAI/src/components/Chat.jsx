import React, { useState } from "react";
import ChatBox from './ChatBox.jsx';
import ChatInput from './ChatInput.jsx';

function Chat() {
    const [messages, setMessages] = useState([]);

    const sendMessage = async (userMessage) => {
        const newMessage = { sender: "You", text: userMessage };
        setMessages((prev) => [...prev, newMessage]);

        try {
            const response = await axios.post("http://127.0.0.1:5001/ask", { question: userMessage });
            const botMessage = { sender: "Chatbot", text: response.data.answer };
            setMessages((prev) => [...prev, botMessage]);
        } catch (error) {
            const errorMessage = { sender: "Chatbot", text: "Error: Unable to connect to the server." };
            setMessages((prev) => [...prev, errorMessage]);
        }
    };

    return (
        <div className="flex justify-center items-center h-screen bg-gray-100">
            <div className="w-full max-w-lg p-4 bg-white shadow-lg rounded-lg">
                <ChatBox messages={messages} />
                <ChatInput onSendMessage={sendMessage} />
            </div>
        </div>
    );
}

export default Chat;