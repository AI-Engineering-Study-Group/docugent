import React, { useEffect, useState } from "react";
import styles from "./Sidebar.module.css";
import { FiPlus, FiX } from "react-icons/fi";

interface HistoryItem {
  sessionId: string;
  timestamp: string;
  preview: string;
}

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onNewChat: () => void;
  onRestoreSession: (sessionId: string) => void;
  activeSessionId: string | null;
}

const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  onNewChat,
  onRestoreSession,
  activeSessionId,
}) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);

  useEffect(() => {
    // Refresh the history list whenever the sidebar is opened or the active session changes.
    if (isOpen) {
      setHistory(
        JSON.parse(localStorage.getItem("apiconf_chat_history") || "[]"),
      );
    }
  }, [isOpen, activeSessionId]);

  return (
    <>
      {isOpen && (
        <div
          className={styles.overlay}
          onClick={onClose}
          role="presentation"
          aria-hidden="true"
        ></div>
      )}
      <aside
        className={`${styles.sidebar} ${isOpen ? styles.open : ""}`}
        role="dialog"
        aria-modal="true"
        aria-label="Chat history navigation"
        aria-hidden={!isOpen}
      >
        <div className={styles.logo}>
          <img
            src="https://apiconf.net/logo2025.svg"
            alt="API Conference 2025"
          />
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close Sidebar"
          >
            <FiX aria-hidden="true" />
          </button>
        </div>

        <button
          type="button"
          className={styles.newChatButton}
          onClick={onNewChat}
          aria-label="Start a new chat"
        >
          <FiPlus aria-hidden="true" />
          <span>New Chat</span>
        </button>

        <div className={styles.recentChatsContainer}>
          <h2 id="recent-chats-heading">Recent Chats</h2>
          <div role="list" aria-labelledby="recent-chats-heading">
            {history.map((item) => (
              <div
                key={item.sessionId}
                className={`${styles.recentChatItem} ${item.sessionId === activeSessionId ? styles.active : ""}`}
                onClick={() => onRestoreSession(item.sessionId)}
                tabIndex={0}
                role="listitem"
                aria-label={`Chat from ${new Date(item.timestamp).toLocaleDateString()}: ${item.preview}`}
              >
                <div className={styles.recentChatItemTitle}>{item.preview}</div>
                <div
                  className={styles.recentChatItemTimestamp}
                  aria-hidden="true"
                >
                  {new Date(item.timestamp).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
