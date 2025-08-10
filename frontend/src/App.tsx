import Chat from "./components/Chat";
import Sidebar from "./components/Sidebar";
import styles from "./App.module.css";
import { useState } from "react";

const saveSessionToHistory = () => {
  const history = JSON.parse(
    localStorage.getItem("apiconf_chat_history") || "[]",
  );
  const sessionId = localStorage.getItem("apiconf_session_id");

  // Avoid adding duplicate or empty sessions
  if (
    sessionId &&
    !history.some((item: { sessionId: string }) => item.sessionId === sessionId)
  ) {
    const timestamp = new Date().toLocaleString();
    const preview =
      localStorage.getItem(`session_preview_${sessionId}`) || "New Chat";
    history.unshift({ sessionId, timestamp, preview });
    localStorage.setItem(
      "apiconf_chat_history",
      JSON.stringify(history.slice(0, 20)),
    ); // Increased limit
  }
};

const SettingsComponent = () => <div>Settings view coming soon.</div>;

const App: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [view, setView] = useState<"chat" | "settings">("chat"); // Simplified view
  const [resetSignal, setResetSignal] = useState(0);

  const toggleSidebar = () => {
    // Save the current session right before opening the sidebar to ensure the list is up-to-date.
    if (!sidebarOpen) {
      saveSessionToHistory();
    }
    setSidebarOpen(!sidebarOpen);
  };

  // Get active session ID from local storage to pass to sidebar
  const activeSessionId = localStorage.getItem("apiconf_session_id");

  const handleNewChat = () => {
    saveSessionToHistory();
    const newSessionId =
      Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
    localStorage.setItem("apiconf_session_id", newSessionId);
    setView("chat");
    if (window.innerWidth <= 768) setSidebarOpen(false); // Close sidebar on mobile
    setResetSignal((s) => s + 1);
  };

  const handleRestoreSession = (sessionId: string) => {
    saveSessionToHistory(); // Save the current session before restoring another
    localStorage.setItem("apiconf_session_id", sessionId);
    setView("chat");
    if (window.innerWidth <= 768) setSidebarOpen(false); // Close sidebar on mobile
    setResetSignal((s) => s + 1);
  };

  return (
    <div className={styles.app}>
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewChat={handleNewChat}
        onRestoreSession={handleRestoreSession}
        activeSessionId={activeSessionId}
      />
      <main>
        {view === "chat" && (
          <Chat onMenuClick={toggleSidebar} resetSignal={resetSignal} />
        )}
        {view === "settings" && <SettingsComponent />}
      </main>
    </div>
  );
};

export default App;
