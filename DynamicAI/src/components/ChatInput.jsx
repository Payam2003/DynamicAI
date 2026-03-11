import React, { useState } from 'react';

function ChatInput({ onSendMessage }) {
    const [input, setInput] = useState("");

    const handleSend = () => {
        if (input.trim()) {
            onSendMessage(input);
            setInput("");
        }
    };

    return (
        <div className="flex border-t border-gray-200 p-2">
             <input
        type="file"
        accept="image/*,.pdf"
        onChange={(e) => setFile(e.target.files[0])}
        className="flex-grow px-3 py-2 border border-gray-300 rounded-md text-sm"
      />
            <button
                onClick={handleSend}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
            >
            Upload
            </button>        
        </div>
    );
}

export default ChatInput;