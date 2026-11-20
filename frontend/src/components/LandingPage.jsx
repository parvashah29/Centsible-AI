import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, Sparkles, TrendingUp, Shield, Zap, ChevronRight, CloudUpload } from 'lucide-react'
import styles from './LandingPage.module.css'

const FEATURES = [
  { icon: <Shield size={20}/>, title: 'Fully Private', desc: 'Your data never leaves your device. AI runs locally on your Mac.' },
  { icon: <Zap size={20}/>, title: 'Instant Analysis', desc: 'Upload your CSV and get a complete spending breakdown in seconds.' },
  { icon: <Sparkles size={20}/>, title: 'Grounded Advice', desc: 'AI advisor cites real financial frameworks — never generic tips.' },
]

export default function LandingPage({ onProfileLoad, user, onLogout }) {
  const [isDragging, setIsDragging] = useState(false)
  const [loading,    setLoading]    = useState(false)
  const [error,      setError]      = useState(null)

  const handleFile = useCallback(async (file) => {
    if (!file || !['text/csv','application/pdf'].includes(file.type) && !file.name.match(/\.(csv|pdf)$/i)) {
      setError('Please upload a valid CSV or PDF bank statement.')
      return
    }
    setError(null)
    setLoading('uploading')
    const fd = new FormData()
    fd.append('file', file)
    try {
      const res  = await fetch('/api/upload', { method: 'POST', body: fd })
      const data = await res.json()
      if (data.success) onProfileLoad(data.profile)
      else setError(data.error || 'Failed to process file.')
    } catch {
      setError('Could not reach the backend. Is the Flask server running?')
    } finally { setLoading(false) }
  }, [onProfileLoad])

  const handleDemo = useCallback(async () => {
    setError(null)
    setLoading('demo')
    try {
      const res  = await fetch('/api/demo')
      const data = await res.json()
      if (data.success) onProfileLoad(data.profile)
      else setError(data.error || 'Failed to load demo.')
    } catch {
      setError('Could not reach the backend. Is the Flask server running?')
    } finally { setLoading(false) }
  }, [onProfileLoad])

  const onDrop = (e) => { e.preventDefault(); setIsDragging(false); handleFile(e.dataTransfer.files[0]) }
  const onInputChange = (e) => handleFile(e.target.files[0])

  return (
    <div className={styles.page}>
      {/* Ambient glow orbs */}
      <div className={styles.orbPurple} />
      <div className={styles.orbBlue}   />

      {/* Hero */}
      <motion.header
        className={styles.hero}
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      >
        {user && (
          <div className={styles.topBar}>
            <span className={styles.welcomeText}>Welcome back, <strong>{user.name?.split(' ')[0]}</strong> 👋</span>
            <button className={styles.signOutBtn} onClick={onLogout}>Sign out</button>
          </div>
        )}
        <div className={styles.logoMark}>
          <TrendingUp size={28} />
        </div>
        <p className={styles.eyebrow}>AI-Powered Financial Intelligence</p>
        <h1 className={styles.headline}>
          Meet <span className="gradient-text">Centsible AI</span>
        </h1>
        <p className={styles.sub}>
          Upload your bank statement. Get a full spending breakdown, personalised advice,
          and a private AI advisor — all running offline on your device.
        </p>
        <div className={styles.heroBadges}>
          <span className="tag tag-purple">100% Free</span>
          <span className="tag tag-green">Runs Locally</span>
          <span className="tag tag-purple">No Data Shared</span>
        </div>
      </motion.header>

      {/* Upload card */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.15, ease: 'easeOut' }}
        className={styles.uploadSection}
      >
        <div
          className={`${styles.dropzone} ${isDragging ? styles.dragging : ''}`}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onDrop}
        >
          <CloudUpload size={40} className={styles.uploadIcon} />
          <h2 className={styles.dropTitle}>Drop your bank statement here</h2>
          <p className={styles.dropSub}>Supports CSV & PDF — HDFC, Chase, Bank of America, Wells Fargo & more</p>

          <label className={`btn-primary ${styles.browseBtn}`} htmlFor="csv-input">
            <Upload size={17} />
            {loading === 'uploading' ? 'Analysing…' : 'Browse File'}
          </label>
          <input
            id="csv-input" type="file" accept=".csv,.pdf"
            style={{ display: 'none' }}
            onChange={onInputChange}
            disabled={!!loading}
          />

          <div className={styles.divider}><span>or</span></div>

          <button
            className={`btn-ghost ${styles.demoBtn}`}
            onClick={handleDemo}
            disabled={!!loading}
          >
            <Sparkles size={17} />
            {loading === 'demo' ? 'Loading demo…' : 'Try Demo Mode'}
            <ChevronRight size={15} className={styles.chevron} />
          </button>

          <AnimatePresence>
            {error && (
              <motion.p
                className={styles.error}
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                {error}
              </motion.p>
            )}
          </AnimatePresence>
        </div>
      </motion.div>

      {/* Features row */}
      <motion.div
        className={styles.features}
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3, ease: 'easeOut' }}
      >
        {FEATURES.map((f, i) => (
          <div key={i} className={`${styles.featureCard} card`}>
            <div className={styles.featureIcon}>{f.icon}</div>
            <h3 className={styles.featureTitle}>{f.title}</h3>
            <p className={styles.featureDesc}>{f.desc}</p>
          </div>
        ))}
      </motion.div>

      <p className={styles.disclaimer}>
        ⚠️ Educational tool only. Not professional financial advice. Always consult a certified financial advisor for major decisions.
      </p>
    </div>
  )
}
