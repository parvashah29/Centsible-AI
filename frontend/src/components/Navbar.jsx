import { TrendingUp, LayoutDashboard, MessageCircle, Home, LogOut } from 'lucide-react'
import styles from './Navbar.module.css'

export default function Navbar({ view, setView, user, onGoHome, onLogout }) {
  return (
    <nav className={styles.nav}>
      {/* Logo — clicking goes back to upload/home */}
      <button className={styles.logo} onClick={onGoHome} title="Back to Home">
        <TrendingUp size={19} className={styles.logoIcon} />
        <span>Centsible<strong>AI</strong></span>
      </button>

      {/* Page tabs */}
      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${view === 'dashboard' ? styles.active : ''}`}
          onClick={() => setView('dashboard')}
        >
          <LayoutDashboard size={15} />
          Dashboard
        </button>
        <button
          className={`${styles.tab} ${view === 'chat' ? styles.active : ''}`}
          onClick={() => setView('chat')}
        >
          <MessageCircle size={15} />
          AI Advisor
        </button>
      </div>

      {/* Right side */}
      <div className={styles.right}>
        <button className={styles.homeBtn} onClick={onGoHome} title="Upload new file">
          <Home size={15} />
          Upload New
        </button>
        {user && (
          <div className={styles.userBadge}>
            <span className={styles.avatar}>{user.name?.[0]?.toUpperCase() ?? '?'}</span>
            <span className={styles.userName}>{user.name?.split(' ')[0]}</span>
          </div>
        )}
        <button className={styles.logoutBtn} onClick={onLogout} title="Sign out">
          <LogOut size={15} />
        </button>
      </div>
    </nav>
  )
}
