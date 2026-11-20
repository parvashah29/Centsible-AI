import { useState, useEffect } from 'react'
import './index.css'
import AuthPage     from './components/AuthPage'
import LandingPage  from './components/LandingPage'
import Dashboard    from './components/Dashboard'
import ChatAdvisor  from './components/ChatAdvisor'
import Navbar       from './components/Navbar'

const SESSION_KEY = 'centsible_session'

export default function App() {
  // 'auth' | 'landing' | 'dashboard' | 'chat'
  const [view,    setView]    = useState('auth')
  const [profile, setProfile] = useState(null)
  const [user,    setUser]    = useState(null)

  // Restore session on mount
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(SESSION_KEY))
      if (saved?.email) { setUser(saved); setView('landing') }
    } catch { /* ignore */ }
  }, [])

  const handleAuth = (userData) => {
    setUser(userData)
    setView('landing')
  }

  const handleLogout = () => {
    localStorage.removeItem(SESSION_KEY)
    setUser(null)
    setProfile(null)
    setView('auth')
  }

  const handleProfileLoad = (data) => {
    setProfile(data)
    setView('dashboard')
  }

  const goHome = () => {
    setProfile(null)
    setView('landing')
  }

  return (
    <>
      {view !== 'auth' && view !== 'landing' && (
        <Navbar
          view={view}
          setView={setView}
          user={user}
          onGoHome={goHome}
          onLogout={handleLogout}
        />
      )}

      {view === 'auth' && (
        <AuthPage onAuth={handleAuth} />
      )}

      {view === 'landing' && (
        <LandingPage
          onProfileLoad={handleProfileLoad}
          user={user}
          onLogout={handleLogout}
        />
      )}

      {view === 'dashboard' && profile && (
        <Dashboard
          profile={profile}
          onOpenChat={() => setView('chat')}
        />
      )}

      {view === 'chat' && profile && (
        <ChatAdvisor profile={profile} />
      )}
    </>
  )
}
