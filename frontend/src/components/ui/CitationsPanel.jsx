// src/components/ui/CitationsPanel.jsx
// ────────────────────────────────────
// Citation Intelligence & BibTeX Exporter component.
// Provides 1-click citation export (BibTeX, APA, IEEE, MLA) for the paper and its bibliography.

import { useState } from 'react'
import {
  BookOpen, Check, Copy, Download, ExternalLink,
  FileCode, Layers, Quote, Search, Sparkles,
} from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'

function CopyCitationBtn({ text, format, className = '' }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      toast.success(`${format} citation copied!`)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <button
      onClick={copy}
      className={clsx('btn btn-secondary btn-sm flex items-center gap-1 text-xs py-1 px-2.5', className)}
      title={`Copy ${format} citation to clipboard`}
    >
      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
      {copied ? 'Copied' : format}
    </button>
  )
}

export default function CitationsPanel({ citations = {}, paperTitle = 'Academic Paper' }) {
  const [activeFormat, setActiveFormat] = useState('bibtex') // 'bibtex' | 'apa' | 'ieee' | 'mla'
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedRef, setExpandedRef] = useState(null)

  const selfCite = citations.paper_citation || {}
  const references = citations.references || []
  const totalRefs = citations.total_references || references.length

  // Filter bibliography by search query
  const filteredReferences = references.filter(r => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      (r.title && r.title.toLowerCase().includes(q)) ||
      (r.authors && r.authors.some(a => a.toLowerCase().includes(q))) ||
      (r.year && r.year.includes(q)) ||
      (r.venue && r.venue.toLowerCase().includes(q))
    )
  })

  // Export full bibliography as .bib file
  const handleExportAllBibtex = () => {
    if (references.length === 0) {
      toast.error('No bibliography entries available to export.')
      return
    }

    const allBibtex = references
      .map(r => r.bibtex || '')
      .filter(Boolean)
      .join('\n\n')

    const blob = new Blob([allBibtex], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${paperTitle.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 30)}_references.bib`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Downloaded .bib bibliography file!')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 1. Cite This Research Paper (Self-Citation) */}
      <div className="card p-6 bg-slate-900/80 border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Quote className="w-4 h-4 text-primary-400" />
              Cite This Paper
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Citation-ready metadata formatted for papers, theses, and reference managers.
            </p>
          </div>

          {/* Format selection pills */}
          <div className="flex items-center gap-1 bg-slate-800 p-1 rounded-lg self-start sm:self-auto">
            {['bibtex', 'apa', 'ieee', 'mla'].map(fmt => (
              <button
                key={fmt}
                onClick={() => setActiveFormat(fmt)}
                className={clsx(
                  'px-2.5 py-1 text-xs font-semibold rounded-md transition-all',
                  activeFormat === fmt
                    ? 'bg-primary-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200',
                )}
              >
                {fmt.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Paper details snippet */}
        <div className="text-xs text-slate-400 space-y-1">
          <p><span className="text-slate-500 font-medium">Title:</span> <strong className="text-slate-200">{paperTitle}</strong></p>
          {selfCite.authors?.length > 0 && (
            <p><span className="text-slate-500 font-medium">Authors:</span> {selfCite.authors.join(', ')}</p>
          )}
          {selfCite.venue && (
            <p><span className="text-slate-500 font-medium">Venue:</span> {selfCite.venue} {selfCite.year ? `(${selfCite.year})` : ''}</p>
          )}
        </div>

        {/* Formatted Code Box */}
        <div className="relative">
          <pre className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {selfCite[activeFormat] || 'Citation format generating...'}
          </pre>
          <div className="absolute top-2.5 right-2.5">
            <CopyCitationBtn text={selfCite[activeFormat] || ''} format={activeFormat.toUpperCase()} />
          </div>
        </div>
      </div>

      {/* 2. Parsed Bibliography & References */}
      <div className="card p-6 bg-slate-900/80 border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-violet-400" />
              Parsed Bibliography & References
              <span className="text-xs font-normal text-slate-400">({totalRefs} detected)</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Extracted from the paper's References section with multi-format citation export.
            </p>
          </div>

          <button
            onClick={handleExportAllBibtex}
            disabled={references.length === 0}
            className="btn btn-secondary btn-sm flex items-center gap-1.5 self-start sm:self-auto text-xs"
          >
            <Download className="w-3.5 h-3.5 text-primary-400" />
            Download .bib File
          </button>
        </div>

        {/* Search input */}
        {references.length > 0 && (
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search references by author, title, or year…"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="input pl-9 text-xs"
            />
          </div>
        )}

        {/* References List */}
        {references.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            <p>No structured bibliography section was detected in this paper.</p>
            <p className="text-xs mt-1 text-slate-600">
              The paper may not include a standard 'References' heading or is an excerpt.
            </p>
          </div>
        ) : filteredReferences.length === 0 ? (
          <p className="text-slate-500 text-xs text-center py-4">No references match your search query.</p>
        ) : (
          <div className="space-y-3 pt-1">
            {filteredReferences.map((ref, idx) => {
              const isExpanded = expandedRef === ref.id

              return (
                <div
                  key={ref.id || idx}
                  className="p-4 bg-slate-950/60 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-all space-y-2.5"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2.5 min-w-0">
                      <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-slate-800 text-primary-400 border border-slate-700/80 flex-shrink-0 mt-0.5">
                        [{ref.id || idx + 1}]
                      </span>
                      <div className="min-w-0">
                        <h4 className="text-sm font-semibold text-slate-200 leading-snug">
                          {ref.title || ref.raw_text.slice(0, 90)}
                        </h4>
                        <p className="text-xs text-slate-400 mt-1">
                          {ref.authors?.length > 0 ? ref.authors.join(', ') : 'Authors not explicitly formatted'}
                          {ref.year ? ` (${ref.year})` : ''}
                          {ref.venue ? ` · ${ref.venue}` : ''}
                        </p>
                      </div>
                    </div>

                    {ref.doi && (
                      <a
                        href={`https://doi.org/${ref.doi}`}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-ghost p-1 text-primary-400 hover:text-primary-300 flex-shrink-0"
                        title="Open DOI resolver"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>

                  {/* Action buttons */}
                  <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-xs flex-wrap gap-2">
                    <button
                      onClick={() => setExpandedRef(isExpanded ? null : ref.id)}
                      className="text-slate-500 hover:text-slate-300 flex items-center gap-1 font-mono text-[11px]"
                    >
                      <FileCode className="w-3 h-3" />
                      {isExpanded ? 'Hide Raw Entry' : 'View BibTeX'}
                    </button>

                    <div className="flex items-center gap-1.5">
                      <CopyCitationBtn text={ref.bibtex} format="BibTeX" />
                      <CopyCitationBtn text={ref.apa} format="APA" />
                      <CopyCitationBtn text={ref.ieee} format="IEEE" />
                    </div>
                  </div>

                  {/* Expanded BibTeX view */}
                  {isExpanded && (
                    <pre className="bg-slate-900/90 p-3 rounded-lg border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto whitespace-pre-wrap animate-fade-in">
                      {ref.bibtex}
                    </pre>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* 3. Detected In-Text Citations & Cross-References */}
      {(citations.in_text_citations || []).length > 0 && (
        <div className="card p-6 bg-slate-900/80 border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                Detected In-Text Citation Anchors
                <span className="text-xs font-normal text-slate-400">({citations.in_text_citations.length} detected)</span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Citation markers like [1] or (Author, Year) detected in the manuscript and mapped to bibliography targets.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {citations.in_text_citations.slice(0, 18).map((inc, i) => (
              <div key={i} className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-xs space-y-1.5 hover:border-slate-700 transition-all">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-primary-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                    {inc.match}
                  </span>
                  <span className="text-[10px] font-semibold text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded">
                    Ref #{inc.ref_id || '—'}
                  </span>
                </div>
                <p className="text-slate-200 font-medium truncate pt-0.5">{inc.title || 'Referenced Work'}</p>
                <p className="text-slate-500 text-[11px] truncate">
                  {inc.authors?.join?.(', ') || 'Authors'} {inc.year ? `(${inc.year})` : ''}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
