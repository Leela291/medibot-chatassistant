import { useState, useRef, useEffect, useCallback } from "react";
import "./App.css";

/* ───────── Helpers ───────── */
const API = "http://localhost:5000/api";

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

/* ───────── Main App ───────── */
let sharedAudioCtx = null;

function App() {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Hello! I'm **MedoAir** — your AI-powered clinical assistant.\n\nI can answer medical inquiries, explain drugs, analyze lab results, and provide research insights from official clinical databases.\n\nYou can also **upload patient records** (PDF, images, CSV) and I'll analyze them for you.",
      time: formatTime(new Date()),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [speakingMessageId, setSpeakingMessageId] = useState(null);
  const [sessionsList, setSessionsList] = useState([]);
  const [isListening, setIsListening] = useState(false);

  const bottomRef = useRef(null);
  const fileInputRef = useRef(null);
  const inputRef = useRef(null);
  const abortControllerRef = useRef(null);
  const recognitionRef = useRef(null);

  // Web Audio click pop synthesizer
  const playClickSound = () => {
    try {
      if (!sharedAudioCtx) {
        sharedAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (sharedAudioCtx.state === "suspended") {
        sharedAudioCtx.resume();
      }
      const osc = sharedAudioCtx.createOscillator();
      const gainNode = sharedAudioCtx.createGain();
      
      osc.connect(gainNode);
      gainNode.connect(sharedAudioCtx.destination);
      
      osc.type = "sine";
      osc.frequency.setValueAtTime(600, sharedAudioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1200, sharedAudioCtx.currentTime + 0.05);
      
      gainNode.gain.setValueAtTime(0.04, sharedAudioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.001, sharedAudioCtx.currentTime + 0.08);
      
      osc.start(sharedAudioCtx.currentTime);
      osc.stop(sharedAudioCtx.currentTime + 0.08);
    } catch (e) {
      console.debug("Web Audio blocked or not supported:", e);
    }
  };


  // Speech Recognition Speech-to-Text
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = "en-US";

      rec.onstart = () => {
        setIsListening(true);
      };

      rec.onend = () => {
        setIsListening(false);
      };

      rec.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput((prev) => (prev ? prev + " " + transcript : transcript));
      };

      recognitionRef.current = rec;
    }
  }, []);

  const toggleListening = () => {
    playClickSound();
    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge.");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
    }
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Fetch all active sessions
  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API}/chat/sessions`);
      const data = await res.json();
      if (data.sessions) {
        setSessionsList(data.sessions);
      }
    } catch (err) {
      console.error("Failed to fetch sessions:", err);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // Load a selected session's history
  const loadSessionHistory = async (id) => {
    if (loading) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/chat/history?session_id=${id}`);
      const data = await res.json();
      if (data.history) {
        const formatted = data.history.map((m) => ({
          role: m.role === "assistant" ? "bot" : "user",
          text: m.content,
          time: formatTime(new Date()),
          sources: m.role === "assistant" ? ["Knowledge Base"] : null,
          id: Math.random(),
        }));
        setMessages(formatted.length > 0 ? formatted : [
          {
            role: "bot",
            text: "🔄 Loaded conversation. How can I help you regarding this medical data today?",
            time: formatTime(new Date()),
          }
        ]);
        setSessionId(id);
      }
    } catch (err) {
      console.error("Failed to load history:", err);
    }
    setLoading(false);
  };

  // Delete a specific session
  const deleteSession = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this consultation history?")) return;
    try {
      await fetch(`${API}/chat/session/${id}`, { method: "DELETE" });
      fetchSessions();
      if (sessionId === id) {
        newSession();
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  };

  const toggleSpeak = (text, msgIndex) => {
    const synth = window.speechSynthesis;

    // Already reading this message → stop
    if (speakingMessageId === msgIndex) {
      synth.cancel();
      setSpeakingMessageId(null);
      return;
    }
    // Stop whatever was playing before
    synth.cancel();
    // Strip markdown and danger level tags so it reads naturally
    const clean = text
      .replace(/\[Danger Level:\s*[^\]]+\]/gi, "")
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/\*(.*?)\*/g, "$1")
      .replace(/#{1,6}\s?/g, "")
      .replace(/\n/g, " ");

    const utterance = new SpeechSynthesisUtterance(clean);
    utterance.lang = "en-US";
    utterance.rate = 1.4;
    utterance.pitch = 1.0;

    utterance.onend  = () => setSpeakingMessageId(null);
    utterance.onerror = () => setSpeakingMessageId(null);

    synth.speak(utterance);
    setSpeakingMessageId(msgIndex);
  };

  /* ── Send message ── */
  const sendMessage = useCallback(async (overrideText) => {
    playClickSound();
    const text = (overrideText || input).trim();
    if (!text && !uploadedFile) return;

    // Cancel any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const userMsg = {
      role: "user",
      text: text || `📎 Uploaded: ${uploadedFile?.name}`,
      time: formatTime(new Date()),
      file: uploadedFile ? uploadedFile.name : null,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    abortControllerRef.current = new AbortController();

    try {
      if (uploadedFile) {
        const formData = new FormData();
        formData.append("file", uploadedFile);
        formData.append("message", text || "Analyze this patient record");
        if (sessionId) formData.append("session_id", sessionId);

        const res = await fetch(`${API}/chat/upload`, {
          method: "POST",
          body: formData,
          signal: abortControllerRef.current.signal,
        });
        const data = await res.json();
        setUploadedFile(null);

        if (data.session_id) {
          setSessionId(data.session_id);
        }

        setMessages((prev) => [
          ...prev,
          {
            role: "bot",
            text: data.answer || data.error || "No response received.",
            time: formatTime(new Date()),
            sources: data.sources,
            isEmergency: data.is_emergency,
            id: Date.now(),
          },
        ]);
        setLoading(false);
      } else {
        const res = await fetch(`${API}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: text,
            session_id: sessionId,
            stream: true,
          }),
          signal: abortControllerRef.current.signal,
        });

        setLoading(false); // Hide spinner as soon as stream connection begins

        const botMsgId = Date.now();
        const initialBotMsg = {
          role: "bot",
          text: "",
          time: formatTime(new Date()),
          sources: [],
          isEmergency: false,
          id: botMsgId,
        };

        setMessages((prev) => [...prev, initialBotMsg]);

        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let done = false;
        let buffer = "";

        while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          if (value) {
            buffer += decoder.decode(value, { stream: !done });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
              const cleanLine = line.trim();
              if (cleanLine.startsWith("data: ")) {
                try {
                  const rawJson = cleanLine.slice(6);
                  const parsed = JSON.parse(rawJson);

                  if (parsed.session_id) {
                    setSessionId(parsed.session_id);
                  }
                  if (parsed.sources) {
                    setMessages((prev) =>
                      prev.map((msg) =>
                        msg.id === botMsgId
                          ? { ...msg, sources: parsed.sources, isEmergency: parsed.is_emergency }
                          : msg
                      )
                    );
                  }
                  if (parsed.token) {
                    setMessages((prev) =>
                      prev.map((msg) =>
                        msg.id === botMsgId
                          ? { ...msg, text: msg.text + parsed.token }
                          : msg
                      )
                    );
                  }
                } catch (e) {
                  console.warn("Error parsing chunk:", e);
                }
              }
            }
          }
        }
      }
      
      // Update session sidebar list
      fetchSessions();
      
    } catch (err) {
      setLoading(false);
      if (err.name === "AbortError") {
        setMessages((prev) => [
          ...prev,
          {
            role: "bot",
            text: "❌️ Request cancelled. Feel free to ask something else!",
            time: formatTime(new Date()),
            isError: true,
          },
        ]);
      } else {
        const offlineText = "⚠️ **MediBot is offline**";
        setMessages((prev) => [
          ...prev,
          {
            role: "bot",
            text: offlineText,
            time: formatTime(new Date()),
            isError: true,
          },
        ]);
      }
    }

    abortControllerRef.current = null;
  }, [input, uploadedFile, sessionId, fetchSessions]);

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
    e.target.value = "";
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);

    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    const validTypes = [
      "application/pdf",
      "image/png",
      "image/jpeg",
      "image/jpg",
      "text/csv",
      "application/vnd.ms-excel",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ];

    // Check if the file matches our valid types or extensions
    if (validTypes.includes(file.type) || file.name.match(/\.(csv|xls|xlsx)$/i)) {
      setUploadedFile(file);
    } else {
      alert("Please upload PDF, Image (PNG/JPG), or CSV/Excel files only.");
    }
  };

  /* ── Render markdown-lite and extract Danger Level Banners ── */
  const extractDangerLevel = (text) => {
    if (!text) return { cleanText: "", level: null };
    const match = text.match(/\[Danger Level:\s*([^\]]+)\]/i);
    if (match) {
      const level = match[1].trim().toLowerCase();
      const cleanText = text.replace(/\[Danger Level:\s*[^\]]+\]/gi, "").trim();
      return { cleanText, level };
    }
    return { cleanText: text, level: null };
  };

  const renderText = (text) => {
    if (!text) return "";
    return text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "<a href='$2' target='_blank' rel='noopener noreferrer' style='color: #0984E3; text-decoration: underline;'>$1</a>")
      .replace(/`([^`]+)`/g, "<code style='background: rgba(0,0,0,0.1); padding: 2px 4px; border-radius: 4px; font-family: monospace;'>$1</code>")
      .replace(/\n/g, "<br/>");
  };

  /* ── Quick topics ── */
  const topics = [
    { label: "Common Cold", icon: "❄️", color: "#6C5CE7" },
    { label: "Flu", icon: "🤧", color: "#0984E3" },
    { label: "Covid19", icon: "🦠", color: "#00B894" },
    { label: "Asthma", icon: "🫁", color: "#FD79A8" },
    { label: "Diabetes", icon: "🍬", color: "#00CEC9" },
    { label: "Dengue Fever", icon: "🦟", color: "#E17055" },
    { label: "Malaria", icon: "🩸", color: "#2e4248" },
    { label: "Tuberculosis", icon: "🦠", color: "#d63031" },
    { label: "Typhoid", icon: "🤒", color: "#e84393" },
    { label: "Diarrhoeal", icon: "🤢", color: "#e17055" },
  ];

  const quickActions = [
    { label: "Symptoms", query: (t) => `What are the symptoms of ${t}?` },
    { label: "Treatment", query: (t) => `How is ${t} treated?` },
    { label: "Prevention", query: (t) => `How to prevent ${t}?` },
    { label: "Food", query: (t) => `What food is recommended for ${t}?` },
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
              <h1 className="logo-text">MedoAir</h1>
              <span className="logo-sub">AI Medical Assistant</span>
            </div>
          </div>
        </div>

        <button className="new-chat-btn" onClick={() => { playClickSound(); newSession(); }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
            <path d="M12 5v14M5 12h14" strokeLinecap="round" />
          </svg>
          New Consultation
        </button>

        {/* ── Consultation History list ── */}
        <div className="sidebar-section history-section">
          <h3 className="section-title">Consultation Sessions</h3>
          <div className="session-history-list">
            {sessionsList.length === 0 ? (
              <div className="empty-history">No conversations yet</div>
            ) : (
              sessionsList.map((s) => (
                <div
                  key={s.session_id}
                  className={`history-card ${sessionId === s.session_id ? "active" : ""}`}
                  onClick={() => { playClickSound(); loadSessionHistory(s.session_id); }}
                >
                  <div className="history-card-body">
                    {/* 👇 Shows ONLY the session title or ID now, keeping it clean */}
                    <span className="history-card-title">
                      {s.title || `Session ${s.session_id.slice(0, 6)}`}
                    </span>
                  </div>
                  {/* 👇 The delete button remains perfectly functional */}
                  <button
                    className="delete-session-btn"
                    onClick={(e) => { playClickSound(); deleteSession(e, s.session_id); }}
                    title="Delete conversation"
                  >
                    ❌
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* ── Quick Topics (Sidebar) ── */}
        <div className="sidebar-section">
          <h3 className="section-title">Quick Topics</h3>
          <div className="topics-slider">
            {topics.map((t) => (
              <div key={t.label} className="topic-btn" style={{ border: `1px solid ${t.color}` }}>
                <div className="topic-icon" style={{ background: `${t.color}20`, color: t.color }}>
                  {t.icon}
                </div>
                <span className="topic-label">{t.label}</span>
                <div className="topic-actions">
                  {quickActions.map((act) => (
                    <button
                      key={act.label}
                      className="quick-action-btn"
                      onClick={(e) => {
                        e.stopPropagation(); // Prevents clicking the card background
                        playClickSound();
                        setInput(act.query(t.label));
                        inputRef.current?.focus();
                      }}
                    >
                      {act.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
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
            onClick={() => { playClickSound(); fileInputRef.current?.click(); }}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="32" height="32">
              <path d="M12 16V4m0 0L8 8m4-4l4 4M4 14v4a2 2 0 002 2h12a2 2 0 002-2v-4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span>Drop files/pics or click</span>
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
            <span>MedoAir System Online</span>
          </div>
        </div>
      </aside>
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Main Chat ── */}
      <main className="chat-main">
        {/* Top Bar */}
        <header className="chat-header">
          <button
            className="toggle-sidebar"
            onClick={() => { playClickSound(); setSidebarOpen(!sidebarOpen); }}
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
            <button className="header-btn" onClick={() => { playClickSound(); newSession(); }} title="New Chat">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
                <path d="M12 5v14M5 12h14" strokeLinecap="round" />
              </svg>
            </button>
          </div>
        </header>

        {/* Messages */}
        <div className="messages-container">
          {messages.map((m, i) => {
            const { cleanText, level } = extractDangerLevel(m.text);
            return (
              <div
                key={i}
                className={`message-row ${m.role} ${m.isEmergency ? "emergency" : ""} ${m.isError ? "error" : ""}`}
              >
                {m.role === "bot" && (
                  <div className="avatar bot-avatar">
                    <span className="bot-emoji">🤖</span>
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

                    {/* 🚨 Visual Danger Alert Banner */}
                    {m.role === "bot" && level && (
                      <div className={`danger-banner ${level}`}>
                        <div className="danger-banner-header">
                          <span className="danger-icon">
                            {level === "emergency" ? "🚨" : level === "high" ? "⚠️" : level === "medium" ? "🍊" : "🛡️"}
                          </span>
                          <span className="danger-title">
                            Danger Level: {level.toUpperCase()}
                          </span>
                        </div>
                        <div className="danger-desc">
                          {level === "emergency" && "CRITICAL: SEEK IMMEDIATE EMERGENCY HOSPITAL CARE / CALL 108 OR 911"}
                          {level === "high" && "WARNING: High danger indicator. Consult a medical specialist immediately."}
                          {level === "medium" && "CAUTION: Moderate indicator. Monitor symptoms closely and book an appointment soon."}
                          {level === "low" && "INFO: Low danger rating. Standard home care and monitoring recommended."}
                        </div>
                      </div>
                    )}

                    <div
                      className="message-text"
                      dangerouslySetInnerHTML={{ __html: renderText(cleanText) }}
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

                  {/* 🔊 Speak button — sits right below the bot reply bubble */}
                  {m.role === "bot" && cleanText && (
                    <button
                      className={`speak-btn ${speakingMessageId === i ? "speaking" : ""}`}
                      onClick={() => { playClickSound(); toggleSpeak(cleanText, i); }}
                      title={speakingMessageId === i ? "Stop reading" : "Read aloud"}
                    >
                      {speakingMessageId === i ? (
                        <>
                          <svg viewBox="0 0 24 24" fill="currentColor" width="13" height="13">
                            <rect x="5" y="5" width="14" height="14" rx="2" />
                          </svg>
                          Stop
                        </>
                      ) : (
                        <>
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="13" height="13">
                            <polygon points="11,5 6,9 2,9 2,15 6,15 11,19" />
                            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" strokeLinecap="round"/>
                            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" strokeLinecap="round"/>
                          </svg>
                          Read aloud
                        </>
                      )}
                    </button>
                  )}
                  
                  <span className="message-time">{m.time}</span>
                </div>
                {m.role === "user" && (
                  <div className="avatar user-avatar">
                    <span className="user-emoji">👤</span>
                  </div>
                )}
              </div>
            );
          })}

          {messages.length === 1 && (
            <div className="welcome-cards">
              <h3 className="welcome-title">Quick Diagnosis References</h3>
              <div className="topics-slider">
                {topics.map((t) => (
                  <div key={t.label} className="topic-btn" style={{ border: `1px solid ${t.color}` }}>
                    <div className="topic-icon" style={{ background: `${t.color}20`, color: t.color }}>
                      {t.icon}
                    </div>
                    <span className="topic-label">{t.label}</span>
                    <div className="topic-actions">
                      {quickActions.map((act) => (
                        <button
                          key={act.label}
                          className="quick-action-btn"
                          onClick={() => {
                            playClickSound();
                            setInput(act.query(t.label));
                            inputRef.current?.focus();
                          }}
                        >
                          {act.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {loading && (
            <div className="message-row bot">
              <div className="avatar bot-avatar">
                <span className="bot-emoji">🤖</span>
              </div>
              <div className="message-content">
                <div className="message-bubble bot typing-bubble">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span className="typing-text">MedoAir is compiling medical analytics...</span>
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
              onClick={() => { 
                playClickSound(); 
                setUploadedFile(null); 
                if (fileInputRef.current) {
                  fileInputRef.current.value = ""; 
                }
              }}
            >
              ❌
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
          MedoAir is an AI diagnostic reference. Self-diagnosis is risky. Always seek a licensed doctor's advice.
        </div>

        {/* Input Area */}
        <div className="input-area">
          <div className="input-wrapper">
            <button className="attach-btn" onClick={() => { playClickSound(); fileInputRef.current?.click(); }} disabled={loading} title="Attach Clinical File">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>

            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && !loading && sendMessage()}
              placeholder={uploadedFile ? `Ask about ${uploadedFile.name}...` : "Describe symptoms, ask about drugs, or upload clinical reports..."}
              disabled={loading}
              className="chat-input"
            />

            {/* 🎙️ Microphone voice-dictation button */}
            <button
              className={`mic-btn ${isListening ? "listening" : ""}`}
              onClick={toggleListening}
              disabled={loading}
              title={isListening ? "Listening... click to stop" : "Speak prompt"}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="20" height="20">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" fill={isListening ? "currentColor" : "none"} />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            </button>

            {loading ? (
              <button className="cancel-btn" onClick={() => {
                playClickSound();
                abortControllerRef.current?.abort();
              }}>
                Cancel
              </button>
            ) : (
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
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;