import React from 'react'
import styles from '../Chat.module.css';
import type { WelcomePromptSuggestionsProps } from '../../../types/DataTypes';


const WelcomePromptSuggestions = ({handleSend}:WelcomePromptSuggestionsProps) => {

  return (
     <div className={styles.welcome}>
              <h1>Welcome!</h1>
              <p>Your friendly assistant for the API Conference 2025 in Lagos. Ask me about speakers, schedules, and more!</p>
              <div className={styles.promptSuggestions}>
                <button className={styles.promptButton} onClick={() => handleSend('Who are the main speakers?')}>
                  Who are the main speakers?
                </button>
                <button className={styles.promptButton} onClick={() => handleSend('What is the conference schedule?')}>
                  What is the conference schedule?
                </button>
                <button className={styles.promptButton} onClick={() => handleSend('How do I get to the venue?')}>
                  How do I get to the venue?
                </button>
              </div>
            </div>
  )
}

export default WelcomePromptSuggestions