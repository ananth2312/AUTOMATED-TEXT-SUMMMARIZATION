// src/pages/DashboardPage.jsx
// ────────────────────────────
// Main authenticated dashboard with real backend metrics.

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'
import {
  BookOpen, Clock, FileText, Plus, TrendingUp,
} from 'lucide-react'
import { analysesApi } from '../services/api'
import { useAuth } from '../context/AuthContext'

function StatCard({ icon: Icon, label, value, color = 'primary' }) {
  const colorMap = {
    primary: 'text-primary-400 bg-primary-900/30',
    emerald: 'text-emerald-400 bg-emerald-900/30',
    amber:   'text-amber-400   bg-amber-900/30',
    violet:  'text-violet-400  bg-violet-900/30',
  }
  return (
    <div className="stat-card">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${colorMap[color]}`}>
        <Icon className="w-5 h-5" />
      </div>
      <p className="stat-value">{value ?? '—'}</p>
      <p className="stat-label">{label}</p>
    </div>
  )
}

function AnalysisRow({ item }) {
  const date = item.created_at
    ? new Date(item.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
    : '—'
  return (
    <Link
      to={`/analyses/${item._id}`}
      className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 transition-colors group"
    >
      <div className="w-8 h-8 rounded-lg bg-primary-900/40 flex items-center justify-center flex-shrink-0">
        <FileText className="w-4 h-4 text-primary-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-200 truncate group-hover:text-white">{item.title}</p>
        <p className="text-xs text-slate-500">{item.word_count?.toLocaleString()} words · {date}</p>
      </div>
      <span className={`badge ${item.summary_type === 'detailed' ? 'badge-info' : item.summary_type === 'concise' ? 'badge-success' : 'badge-purple'}`}>
        {item.summary_type}
      </span>
    </Link>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload?.length) return (
    <div className="card px-3 py-2 text-xs">
      <p className="text-slate-300">{label}</p>
      <p className="text-primary-400 font-medium">{payload[0].value} analyses</p>
    </div>
  )
  return null
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [stats,   setStats]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    analysesApi.dashboard()
      .then(r => setStats(r.data))
      .catch(() => setError('Could not load dashboard data.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center py-24">
      <div className="spinner w-8 h-8" />
    </div>
  )

  if (error) return (
    <div className="card p-6 border-red-800/30 bg-red-900/10 text-red-300 text-sm">{error}</div>
  )

  const chartData = (stats?.analyses_by_day || []).map(d => ({
    date: d.date.slice(5),   // "MM-DD"
    count: d.count,
  }))

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Welcome back, {user?.name?.split(' ')[0]}
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">Here&apos;s your research activity overview</p>
        </div>
        <Link to="/upload" className="btn btn-primary">
          <Plus className="w-4 h-4" />
          New Analysis
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={FileText}   label="Papers Analysed"   value={stats?.total_documents ?? 0}  color="primary" />
        <StatCard icon={BookOpen}   label="Total Analyses"    value={stats?.total_analyses  ?? 0}  color="violet" />
        <StatCard icon={TrendingUp} label="Words Processed"   value={(stats?.total_words_processed ?? 0).toLocaleString()} color="emerald" />
        <StatCard icon={Clock}      label="Days of Activity"  value={(stats?.analyses_by_day || []).length} color="amber" />
      </div>

      {/* Activity Chart + Recent Analyses */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* Chart */}
        <div className="card p-5 lg:col-span-3">
          <h2 className="section-title">Analysis Activity (last 30 days)</h2>
          {chartData.length === 0 ? (
            <div className="h-40 flex items-center justify-center text-slate-500 text-sm">
              No activity yet. Upload a paper to get started!
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Recent analyses */}
        <div className="card p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title mb-0">Recent Analyses</h2>
            <Link to="/library" className="text-xs text-primary-400 hover:text-primary-300">View all →</Link>
          </div>
          {(stats?.recent_analyses || []).length === 0 ? (
            <div className="text-slate-500 text-sm py-6 text-center">
              No analyses yet.
              <br />
              <Link to="/upload" className="text-primary-400 hover:underline mt-1 inline-block">Upload a paper</Link>
            </div>
          ) : (
            <div className="space-y-1">
              {(stats?.recent_analyses || []).map(item => (
                <AnalysisRow key={item._id} item={item} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Link to="/upload" className="card-hover p-5 flex items-center gap-4 group">
          <div className="w-12 h-12 rounded-xl bg-primary-600/20 flex items-center justify-center flex-shrink-0 group-hover:bg-primary-600/30 transition-colors">
            <Plus className="w-6 h-6 text-primary-400" />
          </div>
          <div>
            <p className="font-semibold text-white">Analyse a Paper</p>
            <p className="text-sm text-slate-400">Upload a PDF or paste text</p>
          </div>
        </Link>
        <Link to="/library" className="card-hover p-5 flex items-center gap-4 group">
          <div className="w-12 h-12 rounded-xl bg-violet-600/20 flex items-center justify-center flex-shrink-0 group-hover:bg-violet-600/30 transition-colors">
            <BookOpen className="w-6 h-6 text-violet-400" />
          </div>
          <div>
            <p className="font-semibold text-white">Research Library</p>
            <p className="text-sm text-slate-400">Browse your analysis history</p>
          </div>
        </Link>
      </div>
    </div>
  )
}
