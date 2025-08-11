import React, { useEffect, useState } from 'react';
import styles from './Sidebar.module.css';
import { FiPlus, FiX } from 'react-icons/fi';

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
  onViewChange: (view: 'chat' | 'settings' | 'literature') => void;
  currentView: 'chat' | 'settings' | 'literature';
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, onNewChat, onRestoreSession, activeSessionId, onViewChange, currentView }) => {
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

        <div className={styles.navigationContainer}>
          <h3>Navigation</h3>
          <button 
            className={`${styles.navButton} ${currentView === 'chat' ? styles.active : ''}`}
            onClick={() => onViewChange('chat')}
          >
            💬 Chat
          </button>
          <button 
            className={`${styles.navButton} ${currentView === 'literature' ? styles.active : ''}`}
            onClick={() => onViewChange('literature')}
          >
            📚 Literature Review
          </button>
          <button 
            className={`${styles.navButton} ${currentView === 'settings' ? styles.active : ''}`}
            onClick={() => onViewChange('settings')}
          >
            ⚙️ Settings
          </button>
        </div>

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