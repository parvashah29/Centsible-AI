import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { TrendingUp, Mail, Lock, User, Eye, EyeOff, ArrowRight } from 'lucide-react'
import styles from './AuthPage.module.css'

const USERS_KEY = 'centsible_users'
const SESSION_KEY = 'centsible_session'

function getUsers() {
  try { return JSON.parse(localStorage.getItem(USERS_KEY) || '{}') } catch { return {} }
}

export default function AuthPage({ onAuth }) {
  const [tab,        setTab]        = useState('login')   // 'login' | 'register'
  const [name,       setName]       = useState('')
  const [email,      setEmail]      = useState('')
  const [password,   setPassword]   = useState('')
  const [showPass,   setShowPass]   = useState(false)
  const [error,      setError]      = useState(null)
  const [loading,    setLoading]    = useState(false)

  const validate = () => {
    if (tab === 'register' && !name.trim())       return 'Please enter your name.'
    if (!email.includes('@'))                     return 'Enter a valid email address.'
    if (password.length < 6)                      return 'Password must be at least 6 characters.'
    return null
  }

  const hashPass = (p) => btoa(encodeURIComponent(p)) // lightweight obfuscation for demo

  const handleSubmit = (e) => {
    e.preventDefault()
    setError(null)
    const err = validate()
    if (err) { setError(err); return }

    setLoading(true)
    const users = getUsers()

    setTimeout(() => {           // simulate network delay
      if (tab === 'register') {
        if (users[email]) { setError('An account with this email already exists.'); setLoading(false); return }
        users[email] = { name: name.trim(), hash: hashPass(password) }
        localStorage.setItem(USERS_KEY, JSON.stringify(users))
        localStorage.setItem(SESSION_KEY, JSON.stringify({ email, name: name.trim() }))
        onAuth({ email, name: name.trim() })
      } else {
        const user = users[email]
        if (!user || user.hash !== hashPass(password)) {
          setError('Incorrect email or password.')
          setLoading(false)
          return
        }
        localStorage.setItem(SESSION_KEY, JSON.stringify({ email, name: user.name }))
        onAuth({ email, name: user.name })
      }
      setLoading(false)
    }, 600)
  }

  return (
    <div className={styles.page}>
      <div className={styles.orbPurple} />
      <div className={styles.orbBlue}   />

      <motion.div
        className={styles.card}
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Logo */}
        <div className={styles.logo}>
          <div className={styles.logoMark}><TrendingUp size={22}/></div>
          <span>Centsible<strong>AI</strong></span>
        </div>

        <p className={styles.tagline}>Your private AI financial advisor</p>

        {/* Tabs */}
        <div className={styles.tabs}>
          {['login','register'].map(t => (
            <button
              key={t}
              className={`${styles.tab} ${tab === t ? styles.activeTab : ''}`}
              onClick={() => { setTab(t); setError(null) }}
            >
              {t === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.form
            key={tab}
            onSubmit={handleSubmit}
            className={styles.form}
            initial={{ opacity: 0, x: tab === 'login' ? -12 : 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {tab === 'register' && (
              <div className={styles.field}>
                <label className={styles.label}><User size={14}/> Full Name</label>
                <input
                  className={styles.input}
                  type="text"
                  placeholder="Alex Johnson"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  autoFocus
                />
              </div>
            )}

            <div className={styles.field}>
              <label className={styles.label}><Mail size={14}/> Email</label>
              <input
                className={styles.input}
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                autoFocus={tab === 'login'}
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}><Lock size={14}/> Password</label>
              <div className={styles.passWrap}>
                <input
                  className={styles.input}
                  type={showPass ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                />
                <button type="button" className={styles.eyeBtn} onClick={() => setShowPass(v => !v)}>
                  {showPass ? <EyeOff size={16}/> : <Eye size={16}/>}
                </button>
              </div>
            </div>

            <AnimatePresence>
              {error && (
                <motion.p
                  className={styles.error}
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                >
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            <button
              className={`btn-primary ${styles.submitBtn}`}
              type="submit"
              disabled={loading}
            >
              {loading ? 'Please wait…' : tab === 'login' ? 'Sign In' : 'Create Account'}
              {!loading && <ArrowRight size={16}/>}
            </button>

            <p className={styles.switchHint}>
              {tab === 'login'
                ? <span>New here? <button type="button" className={styles.link} onClick={() => { setTab('register'); setError(null) }}>Create an account</button></span>
                : <span>Already have an account? <button type="button" className={styles.link} onClick={() => { setTab('login'); setError(null) }}>Sign in</button></span>
              }
            </p>
          </motion.form>
        </AnimatePresence>

        <p className={styles.privacyNote}>
          🔒 All data stays on your device. No server-side accounts.
        </p>
      </motion.div>
    </div>
  )
}
