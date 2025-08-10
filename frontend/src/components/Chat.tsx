import { FiMenu, FiSend } from "react-icons/fi";
import React, { useCallback, useEffect, useRef, useState } from "react";

import ReactMarkdown from "react-markdown";
import TypingIndicator from "./TypingIndicator";
import remarkGfm from "remark-gfm";
import styles from "./Chat.module.css";

interface Message {
  text: string;
  sender: "user" | "bot";
  timestamp: string;
}

interface ChatProps {
  onMenuClick: () => void;
  resetSignal?: number;
}

const Chat: React.FC<ChatProps> = ({ onMenuClick, resetSignal }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [processedMessages, setProcessedMessages] = useState<Set<string>>(
    new Set(),
  );
  const [hasProcessedUrlMessage, setHasProcessedUrlMessage] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getOrCreateId = (key: string) => {
    let id = localStorage.getItem(key);
    if (!id) {
      id =
        Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
      localStorage.setItem(key, id);
    }
    return id;
  };
  const userId = getOrCreateId("apiconf_user_id");
  const sessionId = getOrCreateId("apiconf_session_id");

  const handleSend = useCallback(
    async (messageToSend: string) => {
      if (!messageToSend.trim()) return;

      // Save the first user message as the preview for the history
      const isFirstUserMessage =
        messages.filter((m) => m.sender === "user").length === 0;
      if (isFirstUserMessage) {
        localStorage.setItem(`session_preview_${sessionId}`, messageToSend);
      }

      if (processedMessages.has(messageToSend)) {
        console.log("Message already processed:", messageToSend);
        return;
      }

      console.log("Sending message to /api/v1/agents/chat:", messageToSend);

      const userMessage: Message = {
        text: messageToSend,
        sender: "user",
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };

      setMessages((prevMessages) => [...prevMessages, userMessage]);
      setIsTyping(true);
      setError(null);

      try {
        const response = await fetch("/api/v1/agents/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: messageToSend,
            user_id: userId,
            session_id: sessionId,
          }),
        });

        if (!response.ok) {
          throw new Error(`Network response was not ok: ${response.status}`);
        }

        const result = await response.json();
        console.log("API response:", result);

        const botMessage: Message = {
          text: result.data.response,
          sender: "bot",
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        };

        setMessages((prevMessages) => [...prevMessages, botMessage]);
        setProcessedMessages((prev) => new Set(prev).add(messageToSend));

        // Clear URL parameters after processing
        if (window.location.search) {
          window.history.replaceState(
            {},
            document.title,
            window.location.pathname,
          );
        }
      } catch (error) {
        console.error("Error fetching chat response:", error);
        setError(
          "Sorry, I seem to be having trouble connecting. Please try again later.",
        );
        const errorMessage: Message = {
          text: "Sorry, I seem to be having trouble connecting. Please try again later.",
          sender: "bot",
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        };
        setMessages((prevMessages) => [...prevMessages, errorMessage]);
      } finally {
        setIsTyping(false);
      }
    },
    [processedMessages, userId, sessionId, messages],
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSend(input);
    setInput("");
  };

  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Handle URL parameter from external page
  useEffect(() => {
    if (hasProcessedUrlMessage) return;

    console.log("=== URL DEBUGGING ===");
    console.log("Current URL:", window.location.href);
    console.log("Search params:", window.location.search);
    console.log("Pathname:", window.location.pathname);

    // Use native URLSearchParams to ensure we get the URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const messageFromUrl = urlParams.get("message");

    console.log("All URL params:", Object.fromEntries(urlParams));
    console.log("Message from URL:", messageFromUrl);

    if (messageFromUrl) {
      const decodedMessage = decodeURIComponent(messageFromUrl);
      console.log("Decoded message:", decodedMessage);
      console.log("About to send message to API...");

      setHasProcessedUrlMessage(true);

      // Add a small delay to ensure the component is fully mounted
      setTimeout(() => {
        handleSend(decodedMessage);
      }, 100);
    } else {
      console.log("No message parameter found in URL");
    }
  }, [handleSend, hasProcessedUrlMessage]);

  useEffect(() => {
    // A reset signal tells the chat to clear its messages.
    // This is used for starting a new chat or restoring an old one.
    if (resetSignal !== undefined && resetSignal > 0) {
      setMessages([]);
      setProcessedMessages(new Set());
    }
  }, [resetSignal]);

  return (
    <div
      className={styles.chat}
      aria-label="Chat with Ndu, your assistant for the API Conference 2025"
    >
      <div className={styles.chatHeader}>
        <button
          type="button"
          className={styles.menuButton}
          onClick={onMenuClick}
          aria-label="Open menu"
        >
          <FiMenu aria-hidden="true" />
        </button>
        <h1 className={styles.chatTitle}>Chat with Ndu</h1>
      </div>
      <section className={styles.content} aria-labelledby="chat-title">
        <div
          className={styles.messages}
          role="log"
          aria-live="polite"
          aria-relevant="additions"
        >
          {messages.length === 0 ? (
            <div className={styles.welcome}>
              <h2>Welcome!</h2>
              <p>
                Your friendly assistant for the API Conference 2025 in Lagos.
                Ask me about speakers, schedules, and more!
              </p>
              <div className={styles.promptSuggestions}>
                <button
                  type="button"
                  className={styles.promptButton}
                  onClick={() => handleSend("Who are the main speakers?")}
                  aria-label="Ask: Who are the main speakers?"
                >
                  Who are the main speakers?
                </button>
                <button
                  type="button"
                  className={styles.promptButton}
                  onClick={() => handleSend("What is the conference schedule?")}
                  aria-label="Ask: What is the conference schedule?"
                >
                  What is the conference schedule?
                </button>
                <button
                  type="button"
                  tabIndex={0}
                  className={styles.promptButton}
                  onClick={() => handleSend("How do I get to the venue?")}
                  aria-label="Ask: How do I get to the venue?"
                >
                  How do I get to the venue?
                </button>
              </div>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div
                key={index}
                className={`${styles.message} ${
                  msg.sender === "user" ? styles.user : styles.bot
                }`}
                role={msg.sender === "user" ? "status" : "article"}
                aria-label={`${msg.sender === "user" ? "You said" : "Assistant responded"} at ${msg.timestamp}`}
              >
                <div className={styles.messageContent}>
                  {msg.sender === "bot" ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.text}
                    </ReactMarkdown>
                  ) : (
                    msg.text
                  )}
                </div>
                <div className={styles.timestamp} aria-hidden="true">
                  {msg.timestamp}
                </div>
              </div>
            ))
          )}
          {isTyping && (
            <div
              className={`${styles.message} ${styles.bot} ${styles.typing}`}
              aria-live="polite"
              aria-busy="true"
            >
              <TypingIndicator aria-hidden="true" />
              <span>Ndu is typing...</span>
            </div>
          )}
          {error && (
            <p className={styles.error} role="alert" aria-live="assertive">
              {error}
            </p>
          )}
          <div ref={messagesEndRef} aria-hidden="true" />
        </div>
      </section>
      <section className={styles.inputArea} aria-label="Message input">
        <form onSubmit={handleSubmit}>
          <div className={styles.inputForm}>
            <label htmlFor="askQuestion" className={styles.srOnly}>
              Ask Something
            </label>
            <input
              type="text"
              id="askQuestion"
              className={styles.inputField}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask something..."
              aria-required="true"
              aria-describedby="input-instructions"
            />
            <button
              type="submit"
              className={styles.sendButton}
              aria-label="Send message"
            >
              <FiSend aria-hidden="true" />
            </button>
          </div>
        </form>
        <div id="input-instructions" className={styles.srOnly}>
          Press Enter to send, or Ctrl+Enter for quick send
        </div>
      </section>
    </div>
  );
};

export default Chat;
