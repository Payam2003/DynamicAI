import React, { useRef, useState, useEffect } from "react";
import "../css/ChatbotUploadForm.css";
import ChecklistBlock from "./ChecklistBlock";
import SliderBlock from "./SliderBlock";

function DynamicUIRenderer({ components, stepId, onSubmitAction, disabled }) {
  return (
    <div className="dynamic-ui-wrapper">
      {components.map((component, index) => {
        if (component.component === "button_group") {
          return (
            <div key={`${stepId}-${index}`} className="dynamic-ui-block">
              {component.label && (
                <p className="dynamic-ui-label">{component.label}</p>
              )}

              <div className="chat-options">
                {component.options?.map((option) => (
                  <button
                    key={option}
                    type="button"
                    className="option-btn"
                    onClick={() =>
                      onSubmitAction({
                        stepId,
                        actionType: "button_group_submit",
                        payload: {
                          selected_option: option,
                        },
                      })
                    }
                    disabled={disabled}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          );
        }

        if (component.component === "checklist") {
          return (
            <ChecklistBlock
              key={`${stepId}-${index}`}
              component={component}
              stepId={stepId}
              onSubmitAction={onSubmitAction}
              disabled={disabled}
            />
          );
        }

        if (component.component === "slider") {
          return (
            <SliderBlock
              key={`${stepId}-${index}`}
              component={component}
              stepId={stepId}
              onSubmitAction={onSubmitAction}
              disabled={disabled}
            />
          );
        }

        return null;
      })}
    </div>
  );
}

function ChatbotUploadForm() {
  const inputRef = useRef(null);
  const [items, setItems] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [isBotThinking, setIsBotThinking] = useState(false);

  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: "bot",
      text: "Ciao! Carica un file e ti aiuterò ad analizzarlo. Puoi anche continuare la conversazione dopo l'upload.",
      ui_components: [],
      step_id: null,
      isError: false,
      isLoading: false,
    },
  ]);

  useEffect(() => {
    return () => {
      items.forEach((item) => {
        if (item.preview) URL.revokeObjectURL(item.preview);
      });
    };
  }, [items]);

  const accept = ".png,.jpg,.jpeg,.pdf,.txt";

  const isImage = (file) => file.type.startsWith("image/");

  const addBotMessage = (
    text,
    ui_components = [],
    isError = false,
    step_id = null
  ) => {
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        sender: "bot",
        text,
        ui_components,
        step_id,
        isError,
        isLoading: false,
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
        ui_components: [],
        step_id: null,
        isError: false,
        isLoading: false,
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
        ui_components: [],
        step_id: null,
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
        throw new Error(
          data?.reply || data?.error || data?.detail || "Upload fallito"
        );
      }

      if (data?.session_id) {
        setSessionId(data.session_id);
      }

      setMessages((prev) =>
        prev.map((message) =>
          message.id === thinkingMessageId
            ? {
                ...message,
                text: data?.reply || "Ho analizzato il file",
                ui_components: data?.ui_components || [],
                step_id: data?.step_id || null,
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
                text: err.message || "Qualcosa è andato storto durante l'upload.",
                ui_components: [],
                step_id: null,
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

  const handleDynamicAction = async ({ stepId, actionType, payload }) => {
    if (!sessionId) {
      addBotMessage(
        "Nessuna sessione attiva trovata. Per favore carica e invia un file prima.",
        [],
        true
      );
      return;
    }

    const userText =
      payload?.selected_option ||
      (Array.isArray(payload?.selected_options)
        ? payload.selected_options.join(", ")
        : null) ||
      payload?.value ||
      "User interaction";

    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        sender: "user",
        text: userText,
        ui_components: [],
        step_id: null,
        isError: false,
        isLoading: false,
      },
    ]);

    const thinkingMessageId = crypto.randomUUID();

    setMessages((prev) => [
      ...prev,
      {
        id: thinkingMessageId,
        sender: "bot",
        text: "...",
        ui_components: [],
        step_id: null,
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
          step_id: stepId,
          action_type: actionType,
          payload,
        }),
      });

      let data = null;
      try {
        data = await res.json();
      } catch {
        data = null;
      }

      if (!res.ok) {
        throw new Error(
          data?.reply || data?.error || data?.detail || "Richiesta fallita per il passo successivo."
        );
      }

      setMessages((prev) =>
        prev.map((message) =>
          message.id === thinkingMessageId
            ? {
                ...message,
                text: data?.reply || "Ecco il passo successivo",
                ui_components: data?.ui_components || [],
                step_id: data?.step_id || null,
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
                text: err.message || "Qualcosa è andato storto durante la fase successiva.",
                ui_components: [],
                step_id: null,
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
          <p>Carica un file e continua la conversazione</p>
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

                {message.ui_components &&
                  message.ui_components.length > 0 &&
                  !message.isLoading && (
                    <DynamicUIRenderer
                      components={message.ui_components}
                      stepId={message.step_id}
                      onSubmitAction={handleDynamicAction}
                      disabled={isBotThinking}
                    />
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
                  Rimuovi
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
            <span className="upload-text">Carica un'immagine o un file</span>

            <input
              ref={inputRef}
              type="file"
              accept={accept}
              multiple
              className="hidden-input"
              onChange={(e) => {
                addFiles(e.target.files);
                e.target.value = "";
              }}
              disabled={isBotThinking}
            />
          </div>

          <button
            type="submit"
            className="send-btn"
            disabled={!items.length || isBotThinking}
          >
            {isBotThinking ? "..." : "Invia"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatbotUploadForm;