import React, { useRef, useState } from "react";
import "./ChatbotUploadForm.css";

export default function ChatbotUploadForm() {
  const inputRef = useRef(null);
  const [items, setItems] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [isBotThinking, setIsBotThinking] = useState(false);

  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: "bot",
      text: "Hi! Upload an image and I’ll help guide you through the task.",
      options: [],
      isError: false,
    },
  ]);

  const accept = ".png,.jpg,.jpeg,.gif,.webp,.pdf,.doc,.docx,.xls,.xlsx,.txt";

  const isImage = (file) => file.type.startsWith("image/");

  const addBotMessage = (text, options = [], isError = false) => {
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        sender: "bot",
        text,
        options,
        isError,
      },
    ]);
  };

  const addFiles = (fileList) => {
    if (!fileList || !fileList.length) return;

    const next = Array.from(fileList).map((file) => ({
      id: `${file.name}-${file.size}-${file.lastModified}-${crypto.randomUUID()}`,
      file,
      preview: isImage(file) ? URL.createObjectURL(file) : undefined,
    }));

    setItems((prev) => [...prev, ...next]);

    const uploadedNames = Array.from(fileList)
      .map((file) => file.name)
      .join(", ");

    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        sender: "user",
        text: `Uploaded: ${uploadedNames}`,
        options: [],
        isError: false,
      },
    ]);
  };

  const removeFile = (id) => {
    setItems((prev) => {
      const found = prev.find((item) => item.id === id);
      if (found?.preview) URL.revokeObjectURL(found.preview);
      return prev.filter((item) => item.id !== id);
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!items.length) {
      addBotMessage("Please upload at least one file before sending.", [], true);
      return;
    }

    const thinkingMessageId = crypto.randomUUID();

    setMessages((prev) => [
      ...prev,
      {
        id: thinkingMessageId,
        sender: "bot",
        text: "...",
        options: [],
        isError: false,
        isLoading: true,
      },
    ]);

    setIsBotThinking(true);

    const formData = new FormData();
    items.forEach((item) => formData.append("files", item.file));

    try {
      const res = await fetch("/api/chatbot/upload", {
        method: "POST",
        body: formData,
      });

      let data = null;
      try {
        data = await res.json();
      } catch {
        data = null;
      }

      if (!res.ok) {
        throw new Error(data?.reply || data?.error || "Upload failed.");
      }

      if (data?.session_id) {
        setSessionId(data.session_id);
      }

      setMessages((prev) =>
        prev.map((message) =>
          message.id === thinkingMessageId
            ? {
                ...message,
                text: data?.reply || "I analyzed your file.",
                options: data?.options || [],
                isLoading: false,
                isError: false,
              }
            : message
        )
      );
    } catch (err) {
      console.error(err);

      setMessages((prev) =>
        prev.map((message) =>
          message.id === thinkingMessageId
            ? {
                ...message,
                text: err.message || "Something went wrong while uploading.",
                options: [],
                isLoading: false,
                isError: true,
              }
            : message
        )
      );
    } finally {
      setIsBotThinking(false);
    }
  };

  const handleOptionClick = async (option) => {
    if (!sessionId) {
      addBotMessage("No active session found. Please upload and send a file first.", [], true);
      return;
    }

    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        sender: "user",
        text: option,
        options: [],
        isError: false,
      },
    ]);

    const thinkingMessageId = crypto.randomUUID();

    setMessages((prev) => [
      ...prev,
      {
        id: thinkingMessageId,
        sender: "bot",
        text: "...",
        options: [],
        isError: false,
        isLoading: true,
      },
    ]);

    setIsBotThinking(true);

    try {
      const res = await fetch("/api/chatbot/next-step", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          selected_option: option,
        }),
      });

      let data = null;
      try {
        data = await res.json();
      } catch {
        data = null;
      }

      if (!res.ok) {
        throw new Error(data?.reply || data?.error || "Next step request failed.");
      }

      setMessages((prev) =>
        prev.map((message) =>
          message.id === thinkingMessageId
            ? {
                ...message,
                text: data?.reply || "Here is the next step.",
                options: data?.options || [],
                isLoading: false,
                isError: false,
              }
            : message
        )
      );
    } catch (err) {
      console.error(err);

      setMessages((prev) =>
        prev.map((message) =>
          message.id === thinkingMessageId
            ? {
                ...message,
                text: err.message || "Something went wrong while getting the next step.",
                options: [],
                isLoading: false,
                isError: true,
              }
            : message
        )
      );
    } finally {
      setIsBotThinking(false);
    }
  };

  return (
    <div className="chat-page">
      <div className="chat-shell">
        <div className="chat-header">
          <h1>File Assistant</h1>
          <p>Upload a file or image and continue the conversation below.</p>
        </div>

        <div className="chat-window">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`chat-row ${message.sender === "user" ? "user" : "bot"}`}
            >
              <div
                className={`chat-bubble ${message.sender} ${message.isError ? "error" : ""}`}
              >
                <p className={message.isLoading ? "thinking-text" : ""}>
                  {message.text}
                </p>

                {message.options && message.options.length > 0 && !message.isLoading && (
                  <div className="chat-options">
                    {message.options.map((option) => (
                      <button
                        key={option}
                        type="button"
                        className="option-btn"
                        onClick={() => handleOptionClick(option)}
                        disabled={isBotThinking}
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {items.length > 0 && (
          <div className="uploaded-files-bar">
            {items.map((item) => (
              <div key={item.id} className="mini-file-card">
                <div className="mini-file-left">
                  {item.preview ? (
                    <img
                      src={item.preview}
                      alt={item.file.name}
                      className="mini-file-preview"
                    />
                  ) : (
                    <div className="mini-file-placeholder">FILE</div>
                  )}
                  <div className="mini-file-meta">
                    <span className="mini-file-name">{item.file.name}</span>
                    <span className="mini-file-size">
                      {(item.file.size / 1024 / 1024).toFixed(2)} MB
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  className="remove-btn"
                  onClick={() => removeFile(item.id)}
                  disabled={isBotThinking}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        <form className="upload-bar" onSubmit={handleSubmit}>
          <div
            className={`compact-upload ${isDragging ? "dragging" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              addFiles(e.dataTransfer.files);
            }}
            onClick={() => !isBotThinking && inputRef.current?.click()}
          >
            <span className="upload-plus">+</span>
            <span className="upload-text">Upload image or file</span>

            <input
              ref={inputRef}
              type="file"
              accept={accept}
              multiple
              className="hidden-input"
              onChange={(e) => addFiles(e.target.files)}
              disabled={isBotThinking}
            />
          </div>

          <button
            type="submit"
            className="send-btn"
            disabled={!items.length || isBotThinking}
          >
            {isBotThinking ? "..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}