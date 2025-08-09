import React, { useEffect, useState } from 'react';
import styles from './Sidebar.module.css';
import { FiPlus, FiX } from 'react-icons/fi';
import type {HistoryItem,SidebarProps} from '../../types/DataTypes'




const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, onNewChat, onRestoreSession, activeSessionId }) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);

  useEffect(() => {
    // Refresh the history list whenever the sidebar is opened or the active session changes.
    if (isOpen) {
      setHistory(JSON.parse(localStorage.getItem('apiconf_chat_history') || '[]'));
    }
  }, [isOpen, activeSessionId]);

  return (
    <>
      {isOpen && <div className={styles.overlay} onClick={onClose}></div>}
      <aside
        className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label="Sidebar navigation"
      >
        <div className={styles.logo}>
          <img src="https://apiconf.net/logo2025.svg" alt="APIConf Logo" />
          <button className={styles.closeButton} onClick={onClose}>
            <FiX />
          </button>
        </div>

        <button className={styles.newChatButton} onClick={onNewChat}>
          <FiPlus />
          New Chat
        </button>

        <div className={styles.recentChatsContainer}>
          <h3>Recent Chats</h3>
          {history.map((item) => (
            <div
              key={item.sessionId}
              className={`${styles.recentChatItem} ${item.sessionId === activeSessionId ? styles.active : ''}`}
              onClick={() => onRestoreSession(item.sessionId)}
            >
              <div className={styles.recentChatItemTitle}>{item.preview}</div>
              <div className={styles.recentChatItemTimestamp}>{new Date(item.timestamp).toLocaleDateString()}</div>
            </div>
          ))}
        </div>
      </aside>
    </>
  );
};

export default Sidebar; 