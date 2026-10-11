// src/pages/LibraryPage.jsx
// ──────────────────────────
// Research library: searchable, sortable list of user analyses.

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertCircle, BookOpen, FileText, Loader2, Search, Trash2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { analysesApi, documentsApi } from '../services/api'
import clsx from 'clsx'

function EmptyState({ search }) {
  return (
    <div className="card p-12 text-center">
      <BookOpen className="w-12 h-12 text-slate-600 mx-auto mb-4" />
      <p className="text-slate-400 font-medium">
        {search ? `No analyses match "${search}"` : 'Your research library is empty'}
      </p>
      <p className="text-slate-500 text-sm mt-1">
        {search ? 'Try a different search term.' : (
          <>Upload a paper to get started. <Link to="/upload" className="text-primary-400 hover:underline">Analyse now →</Link></>
        )}
      </p>
    </div>
  )
}

export default function LibraryPage() {
  const [analyses, setAnalyses] = useState([])
  const [total,    setTotal]    = useState(0)
  const [page,     setPage]     = useState(1)
  const [search,   setSearch]   = useState('')
  const [loading,  setLoading]  = useState(true)
  const [deleting, setDeleting] = useState(null)

  const PAGE_SIZE = 20

  const load = (p = 1, q = search) => {
    setLoading(true)
    analysesApi.list({ page: p, page_size: PAGE_SIZE })
      .then(r => {
        // Client-side title filter (analyses endpoint doesn't have search yet)
        let items = r.data.items
        if (q) items = items.filter(a => a.title.toLowerCase().includes(q.toLowerCase()))
        setAnalyses(items)
        setTotal(q ? items.length : r.data.total)
        setPage(p)
      })
      .catch(() => toast.error('Failed to load library.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(1, '') }, [])

  const handleSearch = (e) => {
    const q = e.target.value
    setSearch(q)
    load(1, q)
  }

  const handleDelete = async (analysis) => {
    if (!window.confirm(`Delete analysis "${analysis.title}"? This cannot be undone.`)) return
    setDeleting(analysis._id)
    try {
      // If there's a linked document, delete it (which cascades analyses)
      if (analysis.document_id) {
        await documentsApi.delete(analysis.document_id)
      }
      setAnalyses(prev => prev.filter(a => a._id !== analysis._id))
      toast.success('Analysis deleted.')
    } catch {
      toast.error('Delete failed.')
    } finally {
      setDeleting(null)
    }
  }

  const fmtDate = (d) => d
    ? new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
    : '—'

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Research Library</h1>
          <p className="text-slate-400 text-sm mt-0.5">{total} analysis{total !== 1 ? 'es' : ''}</p>
        </div>
        <Link to="/upload" className="btn btn-primary btn-sm">+ New Analysis</Link>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input
          id="library-search"
          type="text"
          className="input pl-9"
          placeholder="Search by title…"
          value={search}
          onChange={handleSearch}
        />
      </div>

      {/* Table / List */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-primary-400" />
        </div>
      ) : analyses.length === 0 ? (
        <EmptyState search={search} />
      ) : (
        <div className="card overflow-hidden">
          <div className="hidden sm:grid grid-cols-12 px-4 py-2 border-b border-slate-800
                          text-xs font-medium text-slate-500 uppercase tracking-wider">
            <span className="col-span-5">Title</span>
            <span className="col-span-2">Type</span>
            <span className="col-span-2 text-right">Words</span>
            <span className="col-span-2 text-right">Date</span>
            <span className="col-span-1" />
          </div>

          <div className="divide-y divide-slate-800">
            {analyses.map(a => (
              <div key={a._id} className="grid grid-cols-1 sm:grid-cols-12 items-center
                                          gap-2 px-4 py-3 hover:bg-slate-800/50 transition-colors group">
                <Link to={`/analyses/${a._id}`} className="sm:col-span-5 flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-primary-900/30 flex items-center justify-center flex-shrink-0">
                    <FileText className="w-4 h-4 text-primary-400" />
                  </div>
                  <p className="text-sm font-medium text-slate-200 truncate group-hover:text-white">
                    {a.title}
                  </p>
                </Link>

                <div className="sm:col-span-2 flex sm:block">
                  <span className={clsx(
                    'badge',
                    a.summary_type === 'concise'  && 'badge-success',
                    a.summary_type === 'medium'   && 'badge-purple',
                    a.summary_type === 'detailed' && 'badge-info',
                  )}>
                    {a.summary_type}
                  </span>
                </div>

                <div className="sm:col-span-2 sm:text-right text-sm text-slate-400">
                  {a.word_count?.toLocaleString()}
                </div>

                <div className="sm:col-span-2 sm:text-right text-xs text-slate-500">
                  {fmtDate(a.created_at)}
                </div>

                <div className="sm:col-span-1 flex sm:justify-end">
                  <button
                    onClick={() => handleDelete(a)}
                    disabled={deleting === a._id}
                    className="p-1.5 rounded hover:bg-red-900/30 text-slate-500 hover:text-red-400 transition-colors"
                    title="Delete"
                  >
                    {deleting === a._id
                      ? <Loader2 className="w-4 h-4 animate-spin" />
                      : <Trash2 className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pagination */}
      {!search && total > PAGE_SIZE && (
        <div className="flex justify-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => load(page - 1)}
            className="btn btn-secondary btn-sm"
          >← Prev</button>
          <span className="text-slate-400 text-sm py-1.5 px-3">Page {page}</span>
          <button
            disabled={page * PAGE_SIZE >= total}
            onClick={() => load(page + 1)}
            className="btn btn-secondary btn-sm"
          >Next →</button>
        </div>
      )}
    </div>
  )
}
