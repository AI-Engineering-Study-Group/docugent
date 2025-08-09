export interface Message {
  text: string;
  sender: 'user' | 'bot';
  timestamp: string;
}

export interface HandleSendType {
  (messageToSend: string): Promise<void>;
}

export interface WelcomePromptSuggestionsProps {
  handleSend: HandleSendType;
}

export interface HeaderType {
  onMenuClick: ()=> void
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