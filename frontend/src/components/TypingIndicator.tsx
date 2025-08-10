import React from "react";
import styles from "./TypingIndicator.module.css";

const TypingIndicator: React.FC = () => {
  return (
    <div
      className={styles.typingIndicator}
      role="status"
      aria-live="polite"
      aria-label="Assistant is typing"
    >
      <div className={styles.dot} aria-hidden="true"></div>
      <div className={styles.dot} aria-hidden="true"></div>
      <div className={styles.dot} aria-hidden="true"></div>
    </div>
  );
};

export default TypingIndicator;
