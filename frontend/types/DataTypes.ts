export interface Message {
  text: string;
  sender: 'user' | 'bot';
  timestamp: string;
}

export interface ChatProps {
  onMenuClick: () => void;
  resetSignal?: number;
}

export interface HistoryItem {
  sessionId: string;
  timestamp: string;
  preview: string;
}

export interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onNewChat: () => void;
  onRestoreSession: (sessionId: string) => void;
  activeSessionId: string | null;
}