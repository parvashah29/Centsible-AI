import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, DollarSign, PiggyBank, MessageCircle } from 'lucide-react'
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend,
} from 'recharts'
import styles from './Dashboard.module.css'

const PALETTE = ['#8b5cf6','#6366f1','#10b981','#f59e0b','#f43f5e','#3b82f6','#ec4899','#14b8a6','#84cc16','#fb923c']
const fmt = (n) => `$${Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 })}`

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  return (
    <div className={styles.tooltip}>
      <p className={styles.tooltipLabel}>{payload[0].name}</p>
      <p className={styles.tooltipVal}>{fmt(payload[0].value)}</p>
    </div>
  )
}

export default function Dashboard({ profile, onOpenChat }) {
  const s        = profile.summary
  const cats     = profile.expenses_by_category   || {}
  const monInc   = profile.monthly_income         || {}
  const monExp   = profile.monthly_expenses       || {}
  const bench    = profile.benchmark_50_30_20     || {}
  const merchants = Object.entries(profile.top_merchants || {}).slice(0, 5)
  const momTrend  = profile.mom_expense_change_pct || {}

  // Pie chart data
  const pieData = Object.entries(cats).map(([name, value]) => ({ name, value }))

  // Bar chart data (income vs expenses per month)
  const allMonths = [...new Set([...Object.keys(monInc), ...Object.keys(monExp)])].sort()
  const barData   = allMonths.map(m => ({
    month:    m.slice(2),   // "2026-01" -> "26-01"
    Income:   monInc[m]  || 0,
    Expenses: monExp[m]  || 0,
  }))

  const savingStatus = bench.savings_gap <= 0 ? 'ahead' : 'behind'

  const statCards = [
    {
      label: 'Avg Monthly Income',
      value: fmt(s.avg_monthly_income),
      icon: <DollarSign size={20}/>,
      color: 'green',
    },
    {
      label: 'Avg Monthly Expenses',
      value: fmt(s.avg_monthly_expenses),
      icon: <TrendingDown size={20}/>,
      color: 'red',
    },
    {
      label: 'Savings Rate',
      value: `${s.savings_rate_pct}%`,
      icon: <PiggyBank size={20}/>,
      color: s.savings_rate_pct >= 20 ? 'green' : 'amber',
    },
    {
      label: 'Monthly Net Savings',
      value: fmt(bench.actual_savings ?? (s.avg_monthly_income - s.avg_monthly_expenses)),
      sub: `over ${s.num_months_of_data} months`,
      icon: <TrendingUp size={20}/>,
      color: (bench.actual_savings ?? s.net_savings) >= 0 ? 'green' : 'red',
    },
  ]

  const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } }
  const fadeUp  = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.4 } } }

  return (
    <div className={styles.page}>
      {/* Header row */}
      <motion.div className={styles.header} initial={{opacity:0,y:-12}} animate={{opacity:1,y:0}}>
        <div>
          <h1 className={styles.title}>Financial Dashboard</h1>
          <p className={styles.sub}>{s.num_months_of_data} months of data analysed</p>
        </div>
        <button className="btn-primary" onClick={onOpenChat}>
          <MessageCircle size={17}/>
          Chat with Advisor
        </button>
      </motion.div>

      {/* Stat Cards */}
      <motion.div className={styles.statGrid} variants={stagger} initial="hidden" animate="show">
        {statCards.map((c, i) => (
          <motion.div key={i} className={`${styles.statCard} card`} variants={fadeUp}>
            <div className={`${styles.statIcon} ${styles[`icon_${c.color}`]}`}>{c.icon}</div>
            <p className={styles.statLabel}>{c.label}</p>
            <p className={`${styles.statValue} ${styles[`text_${c.color}`]}`}>{c.value}</p>
          </motion.div>
        ))}
      </motion.div>

      {/* 50/30/20 Benchmark banner */}
      <motion.div
        className={`${styles.benchBanner} ${savingStatus === 'ahead' ? styles.benchGreen : styles.benchAmber}`}
        initial={{opacity:0}} animate={{opacity:1}} transition={{delay:0.3}}
      >
        <TrendingUp size={18}/>
        {savingStatus === 'ahead'
          ? `🟢 You're ahead of your 20% savings target by ${fmt(Math.abs(bench.savings_gap))}/month — great work!`
          : `🔴 You're ${fmt(bench.savings_gap)} short of your 20% savings target (${fmt(bench.savings_target_20pct)}/month). Reduce your wants spend.`
        }
      </motion.div>

      {/* Charts row */}
      <div className={styles.chartsRow}>
        {/* Spending breakdown pie */}
        <motion.div className={`${styles.chartCard} card`} initial={{opacity:0,x:-20}} animate={{opacity:1,x:0}} transition={{delay:0.2}}>
          <h2 className={styles.chartTitle}>Spending Breakdown</h2>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={pieData} innerRadius={60} outerRadius={100} paddingAngle={3} dataKey="value">
                {pieData.map((_, i) => (
                  <Cell key={i} fill={PALETTE[i % PALETTE.length]} stroke="transparent"/>
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip/>}/>
            </PieChart>
          </ResponsiveContainer>
          <div className={styles.legend}>
            {pieData.map((d, i) => (
              <div key={i} className={styles.legendItem}>
                <span className={styles.legendDot} style={{background: PALETTE[i % PALETTE.length]}}/>
                <span className={styles.legendName}>{d.name}</span>
                <span className={styles.legendPct}>{profile.category_pct_of_spending?.[d.name] ?? 0}%</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Monthly income vs expenses bar */}
        <motion.div className={`${styles.chartCard} card`} initial={{opacity:0,x:20}} animate={{opacity:1,x:0}} transition={{delay:0.25}}>
          <h2 className={styles.chartTitle}>Income vs Expenses</h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={barData} barCategoryGap="30%">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false}/>
              <XAxis dataKey="month" tick={{fill:'#64748b', fontSize:12}} axisLine={false} tickLine={false}/>
              <YAxis tick={{fill:'#64748b', fontSize:11}} axisLine={false} tickLine={false} tickFormatter={v=>`$${(v/1000).toFixed(0)}k`}/>
              <Tooltip content={<CustomTooltip/>} cursor={{fill:'rgba(255,255,255,0.03)'}}/>
              <Legend wrapperStyle={{fontSize:'0.8rem', color:'#94a3b8'}}/>
              <Bar dataKey="Income"   fill="#10b981" radius={[4,4,0,0]}/>
              <Bar dataKey="Expenses" fill="#8b5cf6" radius={[4,4,0,0]}/>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Bottom row: Top merchants + MoM trend */}
      <div className={styles.bottomRow}>
        {/* Top merchants */}
        <motion.div className={`${styles.merchantCard} card`} initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:0.35}}>
          <h2 className={styles.chartTitle}>Top Merchants</h2>
          <div className={styles.merchantList}>
            {merchants.map(([name, amt], i) => {
              const maxAmt = merchants[0][1]
              const pct    = (amt / maxAmt) * 100
              return (
                <div key={i} className={styles.merchantRow}>
                  <span className={styles.mRank}>{i + 1}</span>
                  <div className={styles.mInfo}>
                    <span className={styles.mName}>{name.replace(/[A-Z0-9]{3,}-[A-Z0-9]+/g,'').trim()}</span>
                    <div className={styles.mBarWrap}>
                      <motion.div
                        className={styles.mBar}
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ delay: 0.4 + i * 0.06, duration: 0.5 }}
                        style={{ background: PALETTE[i] }}
                      />
                    </div>
                  </div>
                  <span className={styles.mAmt}>{fmt(amt)}</span>
                </div>
              )
            })}
          </div>
        </motion.div>

        {/* MoM trend */}
        <motion.div className={`${styles.trendCard} card`} initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:0.4}}>
          <h2 className={styles.chartTitle}>Month-over-Month Expenses</h2>
          <div className={styles.trendList}>
            {Object.entries(momTrend).map(([month, pct], i) => (
              <div key={i} className={styles.trendRow}>
                <span className={styles.trendMonth}>{month}</span>
                <div className={`styles.trendPill ${pct > 0 ? styles.trendUp : styles.trendDown}`}>
                  {pct > 0 ? <TrendingUp size={14}/> : <TrendingDown size={14}/>}
                  <span>{Math.abs(pct).toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
          {/* savings benchmark detail */}
          <div className={styles.benchDetail}>
            <h3 className={styles.benchHeading}>50/30/20 Targets (monthly)</h3>
            {[
              { label: 'Needs  (50%)', value: bench.needs_budget_50pct },
              { label: 'Wants  (30%)', value: bench.wants_budget_30pct },
              { label: 'Savings(20%)', value: bench.savings_target_20pct },
              { label: 'Actual savings', value: bench.actual_savings },
            ].map((row, i) => (
              <div key={i} className={styles.benchRow}>
                <span className={styles.benchLabel}>{row.label}</span>
                <span className={styles.benchAmt}>{fmt(row.value)}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
