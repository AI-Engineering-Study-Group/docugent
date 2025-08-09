import React from 'react'
import type { InputAreaProps } from '../../../types/DataTypes'
import styles from '../Chat.module.css';
import { FiSend } from 'react-icons/fi';


const InputArea: React.FC <InputAreaProps> = ({input,setInput,handleSubmit}) => {
  return (
    <div className={styles.inputArea}>
        <form onSubmit={handleSubmit} className={styles.inputForm}>
          <input
            type="text"
            className={styles.inputField}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask something..."
          />
          <button type="submit" className={styles.sendButton}>
            <FiSend />
          </button>
        </form>
      </div>
  )
}

export default InputArea