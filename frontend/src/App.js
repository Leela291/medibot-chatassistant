import { useState, useRef, useEffect, useCallback } from "react";
import "./App.css";

/* ───────── Helpers ───────── */
const API = "http://localhost:5000/api";

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/* ───────── Main App ───────── */
function App() {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Hello! I'm **MediBot** — your AI-powered medical assistant.\n\nI can help you with information about **Asthma**, **Dengue**, **Diabetes**, and **Hyperthyroidism**.\n\nYou can also **upload patient records** (PDF, images, CSV) and I'll analyze them for you.",
      time: formatTime(new Date()),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const bottomRef = useRef(null);
  const fileInputRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  /* ── Send message ── */
  const sendMessage = useCallback(async (overrideText) => {
    const text = (overrideText || input).trim();
    if (!text && !uploadedFile) return;

    const userMsg = {
      role: "user",
      text: text || `📎 Uploaded: ${uploadedFile?.name}`,
      time: formatTime(new Date()),
      file: uploadedFile ? uploadedFile.name : null,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      let data;

      if (uploadedFile) {
        // File upload flow
        const formData = new FormData();
        formData.append("file", uploadedFile);
        formData.append("message", text || "Analyze this patient record");
        if (sessionId) formData.append("session_id", sessionId);

        const res = await fetch(`${API}/chat/upload`, {
          method: "POST",
          body: formData,
        });
        data = await res.json();
        setUploadedFile(null);
      } else {
        // Normal chat flow
        const res = await fetch(`${API}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: text,
            session_id: sessionId,
          }),
        });
        data = await res.json();
      }

      if (data.session_id) setSessionId(data.session_id);

      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: data.answer || data.error || "No response received.",
          time: formatTime(new Date()),
          sources: data.sources,
          isEmergency: data.is_emergency,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: "⚠️ Unable to connect to MediBot server. Please make sure the backend is running on port 5000.",
          time: formatTime(new Date()),
          isError: true,
        },
      ]);
    }
    setLoading(false);
    inputRef.current?.focus();
  }, [input, uploadedFile, sessionId]);

  /* ── New session ── */
  const newSession = async () => {
    setMessages([
      {
        role: "bot",
        text: "🔄 New session started! How can I help you today?",
        time: formatTime(new Date()),
      },
    ]);
    setSessionId(null);
    setUploadedFile(null);
  };

  /* ── File handling ── */
  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const validTypes = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      ];
      if (validTypes.includes(file.type) || file.name.endsWith(".csv")) {
        setUploadedFile(file);
      } else {
        alert("Please upload PDF, Image (PNG/JPG), or CSV/Excel files only.");
      }
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setUploadedFile(file);
    }
  };

  /* ── Render markdown-lite ── */
  const renderText = (text) => {
    if (!text) return "";
    return text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\n/g, "<br/>");
  };

  /* ── Quick topics ── */
  const topics = [
    { label: "Asthma", icon: "🫁", color: "#6C5CE7" },
    { label: "Dengue", icon: "🦟", color: "#E17055" },
    { label: "Diabetes", icon: "🩸", color: "#00B894" },
    { label: "Hyperthyroidism", icon: "🦋", color: "#0984E3" },
  ];

  const quickActions = [
    { label: "Symptoms", query: (t) => `What are the symptoms of ${t}?` },
    { label: "Treatment", query: (t) => `How is ${t} treated?` },
    { label: "Prevention", query: (t) => `How to prevent ${t}?` },
    { label: "Emergency Signs", query: (t) => `What are the emergency signs of ${t}?` },
  ];

  return (
    <div className="app-container">
      {/* ── Sidebar ── */}
      <aside className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>
        <div className="sidebar-header">
          <div className="logo-section">
            <div className="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L12 22M2 12L22 12M7 7L17 17M17 7L7 17" strokeLinecap="round" />
              </svg>
            </div>
            <div>
              <h1 className="logo-text">MediBot</h1>
              <span className="logo-sub">AI Medical Assistant</span>
            </div>
          </div>
        </div>

        <button className="new-chat-btn" onClick={newSession}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
            <path d="M12 5v14M5 12h14" strokeLinecap="round" />
          </svg>
          New Conversation
        </button>

        <div className="sidebar-section">
          <h3 className="section-title">Quick Topics</h3>
          {topics.map((t) => (
            <button
              key={t.label}
              className="topic-btn"
              onClick={() => sendMessage(`Tell me about ${t.label}`)}
            >
              <span className="topic-icon" style={{ background: t.color }}>
                {t.icon}
              </span>
              {t.label}
            </button>
          ))}
        </div>

        <div className="sidebar-section">
          <h3 className="section-title">Upload Records</h3>
          <div
            className={`upload-zone ${dragOver ? "drag-over" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="32" height="32">
              <path d="M12 16V4m0 0L8 8m4-4l4 4M4 14v4a2 2 0 002 2h12a2 2 0 002-2v-4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>Drop files here or click</span>
            <span className="upload-hint">PDF, Images, CSV, Excel</span>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.csv,.xls,.xlsx"
              onChange={handleFileSelect}
              hidden
            />
          </div>
        </div>

        <div className="sidebar-footer">
          <div className="status-indicator">
            <div className="status-dot"></div>
            <span>Ollama Connected</span>
          </div>
        </div>
      </aside>

      {/* ── Main Chat ── */}
      <main className="chat-main">
        {/* Top Bar */}
        <header className="chat-header">
          <button
            className="toggle-sidebar"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="22" height="22">
              <path d="M3 12h18M3 6h18M3 18h18" strokeLinecap="round" />
            </svg>
          </button>
          <div className="header-center">
            <h2>Medical Consultation</h2>
            <span className="header-sub">
              {sessionId ? `Session: ${sessionId.slice(0, 8)}...` : "New Session"}
            </span>
          </div>
          <div className="header-actions">
            <button className="header-btn" onClick={newSession} title="New Chat">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
                <path d="M12 5v14M5 12h14" strokeLinecap="round" />
              </svg>
            </button>
          </div>
        </header>

        {/* Messages */}
        <div className="messages-container">
          {messages.length === 1 && (
            <div className="welcome-cards">
              <h3 className="welcome-title">What would you like to know?</h3>
              <div className="cards-grid">
                {topics.map((t) => (
                  <div key={t.label} className="welcome-card" onClick={() => sendMessage(`Tell me about ${t.label}`)}>
                    <div className="card-icon" style={{ background: `${t.color}20`, color: t.color }}>
                      {t.icon}
                    </div>
                    <h4>{t.label}</h4>
                    <div className="card-actions">
                      {quickActions.map((a) => (
                        <button
                          key={a.label}
                          className="card-action-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            sendMessage(a.query(t.label));
                          }}
                        >
                          {a.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div
              key={i}
              className={`message-row ${m.role} ${m.isEmergency ? "emergency" : ""} ${m.isError ? "error" : ""}`}
            >
              {m.role === "bot" && (
                <div className="avatar bot-avatar">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
                    <path d="M12 2L12 22M2 12L22 12" strokeLinecap="round" />
                  </svg>
                </div>
              )}
              <div className="message-content">
                <div className={`message-bubble ${m.role}`}>
                  {m.file && (
                    <div className="file-badge">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                        <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z" strokeLinecap="round" strokeLinejoin="round" />
                        <polyline points="13,2 13,9 20,9" />
                      </svg>
                      {m.file}
                    </div>
                  )}
                  <div
                    className="message-text"
                    dangerouslySetInnerHTML={{ __html: renderText(m.text) }}
                  />
                  {m.sources && m.sources.length > 0 && (
                    <div className="sources-bar">
                      <span className="sources-label">Sources:</span>
                      {m.sources.map((s) => (
                        <span key={s} className="source-tag">
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <span className="message-time">{m.time}</span>
              </div>
              {m.role === "user" && (
                <div className="avatar user-avatar">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
                    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="message-row bot">
              <div className="avatar bot-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
                  <path d="M12 2L12 22M2 12L22 12" strokeLinecap="round" />
                </svg>
              </div>
              <div className="message-content">
                <div className="message-bubble bot typing-bubble">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span className="typing-text">MediBot is thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Uploaded file preview */}
        {uploadedFile && (
          <div className="file-preview-bar">
            <div className="file-preview-info">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z" strokeLinecap="round" strokeLinejoin="round" />
                <polyline points="13,2 13,9 20,9" />
              </svg>
              <span>{uploadedFile.name}</span>
              <span className="file-size">
                ({(uploadedFile.size / 1024).toFixed(1)} KB)
              </span>
            </div>
            <button
              className="remove-file-btn"
              onClick={() => setUploadedFile(null)}
            >
              ✕
            </button>
          </div>
        )}

        {/* Disclaimer */}
        <div className="disclaimer-bar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          MediBot provides general health information only. Always consult a qualified doctor.
        </div>

        {/* Input Area */}
        <div className="input-area">
          <div className="input-wrapper">
            <button
              className="attach-btn"
              onClick={() => fileInputRef.current?.click()}
              title="Upload patient records"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              placeholder={
                uploadedFile
                  ? `Ask about ${uploadedFile.name}...`
                  : "Describe your symptoms or ask a medical question..."
              }
              className="chat-input"
            />
            <button
              className={`send-btn ${(input.trim() || uploadedFile) ? "active" : ""}`}
              onClick={() => sendMessage()}
              disabled={!input.trim() && !uploadedFile}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22,2 15,22 11,13 2,9" />
              </svg>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;