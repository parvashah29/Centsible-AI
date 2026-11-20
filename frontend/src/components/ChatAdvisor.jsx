import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Sparkles, RefreshCw, AlertCircle } from 'lucide-react'
import styles from './ChatAdvisor.module.css'

const STARTER_QUESTIONS = [
  'Where is most of my money going?',
  'Am I saving enough?',
  'How can I reduce food spending?',
  'What is the 50/30/20 rule?',
  'Give me one financial win I can do this week.',
]

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <motion.div
      className={`${styles.msgRow} ${isUser ? styles.userRow : styles.botRow}`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <div className={`${styles.avatar} ${isUser ? styles.avatarUser : styles.avatarBot}`}>
        {isUser ? <User size={16}/> : <Bot size={16}/>}
      </div>
      <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleBot}`}>
        {msg.content}
        {msg.streaming && <span className={styles.cursor}/>}
      </div>
    </motion.div>
  )
}

export default function ChatAdvisor({ profile }) {
  const [messages,  setMessages]  = useState([])
  const [input,     setInput]     = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error,     setError]     = useState(null)
  const bottomRef = useRef(null)
  const inputRef  = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Greet on mount
  useEffect(() => {
    const rate = profile?.summary?.savings_rate_pct ?? 0
    setMessages([{
      role: 'assistant',
      content: `Hi! I'm Centsible, your personal finance advisor. I can see you have a **${rate}% savings rate** — let's dig into your finances together. What would you like to know?`,
    }])
  }, [profile])

  const sendMessage = async (text) => {
    const userMsg = text ?? input.trim()
    if (!userMsg || streaming) return
    setInput('')
    setError(null)

    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setMessages(prev => [...prev, { role: 'assistant', content: '', streaming: true }])
    setStreaming(true)

    try {
      const res = await fetch('/api/chat', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg, profile }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.error || 'Server error')
      }

      const reader = res.body.getReader()
      const dec    = new TextDecoder()
      let buffer   = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += dec.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const payload = JSON.parse(line.slice(6))
          if (payload.error) throw new Error(payload.error)
          if (payload.done)  break
          if (payload.token) {
            setMessages(prev => {
              const copy = [...prev]
              copy[copy.length - 1] = {
                ...copy[copy.length - 1],
                content: copy[copy.length - 1].content + payload.token,
              }
              return copy
            })
          }
        }
      }
    } catch (err) {
      setError(err.message)
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setMessages(prev => {
        const copy = [...prev]
        if (copy[copy.length - 1]?.streaming) {
          copy[copy.length - 1] = { ...copy[copy.length - 1], streaming: false }
        }
        return copy
      })
      setStreaming(false)
      inputRef.current?.focus()
    }
  }

  const handleReset = async () => {
    await fetch('/api/reset', { method: 'POST' })
    const rate = profile?.summary?.savings_rate_pct ?? 0
    setMessages([{
      role: 'assistant',
      content: `Conversation reset! I'm Centsible, your personal finance advisor. Your savings rate is **${rate}%** — what would you like to explore?`,
    }])
    setError(null)
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  return (
    <div className={styles.page}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <div className={styles.sideHeader}>
          <Sparkles size={16}/> Quick Questions
        </div>
        <div className={styles.starters}>
          {STARTER_QUESTIONS.map((q, i) => (
            <button
              key={i}
              className={styles.starter}
              onClick={() => sendMessage(q)}
              disabled={streaming}
            >
              {q}
            </button>
          ))}
        </div>

        {/* Mini profile summary */}
        <div className={styles.miniProfile}>
          <p className={styles.miniLabel}>Your Profile</p>
          <div className={styles.miniRow}>
            <span>Income/mo</span>
            <span>${Number(profile?.summary?.avg_monthly_income ?? 0).toLocaleString('en-US', {maximumFractionDigits:0})}</span>
          </div>
          <div className={styles.miniRow}>
            <span>Expenses/mo</span>
            <span>${Number(profile?.summary?.avg_monthly_expenses ?? 0).toLocaleString('en-US', {maximumFractionDigits:0})}</span>
          </div>
          <div className={styles.miniRow}>
            <span>Savings Rate</span>
            <strong className={profile?.summary?.savings_rate_pct >= 20 ? styles.statGreen : styles.statAmber}>
              {profile?.summary?.savings_rate_pct}%
            </strong>
          </div>
        </div>
      </aside>

      {/* Chat area */}
      <div className={styles.chatPane}>
        <div className={styles.chatHeader}>
          <div className={styles.botInfo}>
            <div className={styles.botAvatar}><Bot size={18}/></div>
            <div>
              <p className={styles.botName}>Centsible</p>
              <p className={styles.botStatus}><span className={styles.dot}/>Online · Mistral 7B · Local</p>
            </div>
          </div>
          <button className={`btn-ghost ${styles.resetBtn}`} onClick={handleReset} title="Reset conversation">
            <RefreshCw size={15}/>
            Reset
          </button>
        </div>

        <div className={styles.messages}>
          <AnimatePresence initial={false}>
            {messages.map((m, i) => <MessageBubble key={i} msg={m}/>)}
          </AnimatePresence>

          {error && (
            <motion.div className={styles.errBanner} initial={{opacity:0}} animate={{opacity:1}}>
              <AlertCircle size={16}/> {error}
            </motion.div>
          )}
          <div ref={bottomRef}/>
        </div>

        <div className={styles.inputArea}>
          <input
            ref={inputRef}
            className={styles.input}
            placeholder="Ask me anything about your finances…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={streaming}
          />
          <button
            className={`${styles.sendBtn} ${streaming ? styles.sendBusy : ''}`}
            onClick={() => sendMessage()}
            disabled={streaming || !input.trim()}
          >
            <Send size={17}/>
          </button>
        </div>
        <p className={styles.disclaimer}>
          Educational tool only · Not professional financial advice
        </p>
      </div>
    </div>
  )
}
