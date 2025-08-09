
import styles from '../Chat.module.css';
import { FiMenu} from 'react-icons/fi';
import type { HeaderType} from '../../../types/DataTypes';

const Header = ({onMenuClick}:HeaderType) => {
  return (
    <div className={styles.chatHeader}>
        <button className={styles.menuButton} onClick={onMenuClick}>
          <FiMenu />
        </button>
        Chat with Ndu
      </div>
  )
}

export default Header