// src/pages/AnalysisPage.jsx
// ───────────────────────────
// Full analysis results viewer with tabs for:
// - Overview & Executive Brief
// - Summary & Source-Linked Evidence
// - Research Methodology & Findings (9 Structured Dimensions)
// - Section-Wise Intelligent Summaries
// - Key Phrases (YAKE)
// - Document Statistics
// - Source Text Preview

import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  AlertTriangle, ArrowLeft, BarChart2, BookOpen, Check,
  CheckCircle2, ChevronDown, ChevronRight, Columns, Copy, Download,
  ExternalLink, Eye, FileText, Key, Layers, Loader2,
  Quote, ShieldCheck, Sparkles, XCircle,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { analysesApi } from '../services/api'
import clsx from 'clsx'
import PdfReaderPanel from '../components/ui/PdfReaderPanel'
import CitationsPanel from '../components/ui/CitationsPanel'
import CitationPopover from '../components/ui/CitationPopover'

const TABS = [
  { id: 'overview',    label: 'Overview',            icon: FileText },
  { id: 'summary',     label: 'Summary & Evidence',  icon: BookOpen },
  { id: 'methodology', label: 'Findings & Methods',  icon: Sparkles },
  { id: 'sections',    label: 'Section Summaries',   icon: Layers   },
  { id: 'citations',   label: 'Citations & BibTeX',  icon: Quote    },
  { id: 'phrases',     label: 'Key Phrases',         icon: Key      },
  { id: 'stats',       label: 'Statistics',          icon: BarChart2 },
  { id: 'source',      label: 'Source',              icon: FileText },
]


function CopyButton({ text, label = 'Copy' }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }
  return (
    <button onClick={copy} className="btn btn-secondary btn-sm flex items-center gap-1.5">
      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
      {copied ? 'Copied' : label}
    </button>
  )
}

function ExportButton({ analysisId, format }) {
  const [loading, setLoading] = useState(false)
  const download = async () => {
    setLoading(true)
    try {
      const fn = format === 'pdf' ? analysesApi.exportPdf : analysesApi.exportTxt
      const res = await fn(analysisId)
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `analysis.${format}`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast.error('Export failed.')
    } finally {
      setLoading(false)
    }
  }
  return (
    <button onClick={download} disabled={loading} className="btn btn-secondary btn-sm flex items-center gap-1.5">
      {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
      .{format.toUpperCase()}
    </button>
  )
}

export default function AnalysisPage() {
  const { analysisId } = useParams()
  const navigate = useNavigate()
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [tab, setTab] = useState('overview')
  const [summaryLevel, setSummaryLevel] = useState('medium')
  const [selectedSentence, setSelectedSentence] = useState(null)
  const [summaryViewMode, setSummaryViewMode] = useState('interactive') // 'interactive' | 'continuous'
  const [methodologyFilter, setMethodologyFilter] = useState('all') // 'all' | 'found' | 'not_stated'
  const [expandedSection, setExpandedSection] = useState(null)
  const [splitView, setSplitView] = useState(false)
  const [pdfPage, setPdfPage] = useState(1)

  useEffect(() => {
    analysesApi.get(analysisId)
      .then(r => {
        setAnalysis(r.data)
        const initialLevel = r.data.summary_type || 'medium'
        setSummaryLevel(initialLevel)
        // Default selected sentence from initial level evidence if available
        const evList = (r.data.evidence_by_level && r.data.evidence_by_level[initialLevel])
          || r.data.summary_sentences_with_evidence || []
        if (evList.length > 0) {
          setSelectedSentence(evList[0])
          if (evList[0].page_number) {
            setPdfPage(evList[0].page_number)
          }
        }
      })

      .catch(() => setError('Analysis not found or access denied.'))
      .finally(() => setLoading(false))
  }, [analysisId])

  // Update selected sentence when summaryLevel changes
  const handleLevelChange = (level) => {
    setSummaryLevel(level)
    if (!analysis) return
    const evList = (analysis.evidence_by_level && analysis.evidence_by_level[level])
      || (level === analysis.summary_type ? analysis.summary_sentences_with_evidence : [])
    if (evList && evList.length > 0) {
      setSelectedSentence(evList[0])
    } else {
      setSelectedSentence(null)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-28 space-y-4">
        <Loader2 className="w-10 h-10 animate-spin text-primary-500" />
        <p className="text-slate-400 text-sm">Loading document intelligence...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card p-6 border-red-800/40 bg-red-950/20 text-red-300 text-sm max-w-lg mx-auto mt-12 text-center space-y-3">
        <AlertTriangle className="w-8 h-8 text-red-400 mx-auto" />
        <p className="font-semibold text-white">{error}</p>
        <button onClick={() => navigate('/library')} className="btn btn-secondary btn-sm">
          Return to Library
        </button>
      </div>
    )
  }

  const a = analysis
  const stats = a.statistics || {}
  const fmt = (n) => n?.toLocaleString?.() ?? n ?? '—'
  const fmtDate = (d) => d ? new Date(d).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' }) : '—'

  const currentSummary = {
    concise:  a.concise_summary,
    medium:   a.medium_summary,
    detailed: a.detailed_summary,
  }[summaryLevel] || a.summary_text || ''

  const currentEvidenceList = (a.evidence_by_level && a.evidence_by_level[summaryLevel])
    || (summaryLevel === a.summary_type ? a.summary_sentences_with_evidence : [])
    || []

  const methFindings = a.methodology_findings || { dimensions: [], total_found: 0, total_dimensions: 9 }
  const filteredDimensions = methFindings.dimensions.filter(d => {
    if (methodologyFilter === 'found') return d.found
    if (methodologyFilter === 'not_stated') return !d.found
    return true
  })

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="flex items-start gap-3">
          <button
            onClick={() => navigate(-1)}
            className="btn btn-ghost p-2 mt-0.5 rounded-lg hover:bg-slate-800"
            title="Go back"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div className="min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold text-white truncate max-w-2xl">
              {a.title}
            </h1>
            <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-slate-400">
              <span>Analysed on {fmtDate(a.created_at)}</span>
              <span>•</span>
              <span className="text-primary-400 font-medium">{stats.word_count ? `${fmt(stats.word_count)} words` : 'Text Document'}</span>
              <span>•</span>
              <span className="inline-flex items-center gap-1 text-emerald-400">
                <ShieldCheck className="w-3.5 h-3.5" /> Extractive TextRank Verified
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
          <button
            onClick={() => setSplitView(s => !s)}
            className={clsx(
              'btn btn-sm flex items-center gap-1.5 transition-all text-xs font-semibold',
              splitView
                ? 'bg-primary-600 text-white shadow-md shadow-primary-950/60 border border-primary-500'
                : 'btn-secondary text-slate-300 hover:text-white',
            )}
            title="Toggle split-screen interactive PDF viewer"
          >
            <Columns className="w-3.5 h-3.5 text-primary-400" />
            {splitView ? 'Exit Split View' : 'Split Reader View'}
          </button>
          <ExportButton analysisId={analysisId} format="txt" />
          <ExportButton analysisId={analysisId} format="pdf" />
        </div>
      </div>

      {/* Warnings Banner */}
      {(a.warnings || []).length > 0 && (
        <div className="card p-4 border-amber-800/40 bg-amber-950/20 space-y-1 rounded-xl">
          {a.warnings.map((w, i) => (
            <div key={i} className="flex items-start gap-2 text-amber-300 text-xs sm:text-sm">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-400" />
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-1.5 overflow-x-auto pb-1 border-b border-slate-800/80 scrollbar-thin">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={clsx(
              'flex items-center gap-2 px-3.5 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all',
              tab === id
                ? 'bg-primary-600/25 text-primary-400 border border-primary-500/40 shadow-sm shadow-primary-950/50'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60',
            )}
          >
            <Icon className="w-4 h-4" />
            <span>{label}</span>
            {id === 'methodology' && methFindings.total_found > 0 && (
              <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30">
                {methFindings.total_found}/9
              </span>
            )}
            {id === 'sections' && (a.section_summaries?.length || a.detected_sections?.length) > 0 && (
              <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-primary-500/20 text-primary-300 rounded-full">
                {a.section_summaries?.length || a.detected_sections?.length}
              </span>
            )}
            {id === 'citations' && (a.citations?.total_references || 0) > 0 && (
              <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-violet-500/20 text-violet-300 rounded-full border border-violet-500/30">
                {a.citations.total_references}
              </span>
            )}
          </button>
        ))}
      </div>


      {/* Interactive Split-Screen Reader & Tab Contents */}
      <div className={clsx(splitView && 'grid grid-cols-1 lg:grid-cols-12 gap-6 items-start')}>
        {splitView && (
          <div className="lg:col-span-5 sticky top-20 z-20">
            <PdfReaderPanel
              documentId={a.document_id}
              pageCount={stats.page_count || a.page_count || 1}
              targetPage={pdfPage}
              syncedSentence={selectedSentence}
              sourceText={a.extracted_text || a.source_text_preview}
            />
          </div>
        )}
        <div className={clsx(splitView ? 'lg:col-span-7 space-y-6 min-w-0' : 'space-y-6')}>
          {/* ──────────────────────────────────────────────────────────── */}
          {/* 1. OVERVIEW TAB */}
          {/* ──────────────────────────────────────────────────────────── */}
      {tab === 'overview' && (
        <div className="space-y-6">
          {/* Quick Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
            <div className="card p-4 bg-slate-900/60 border-slate-800">
              <span className="text-xs text-slate-400">Total Words</span>
              <p className="text-xl font-bold text-white mt-1">{fmt(stats.word_count)}</p>
              <span className="text-[11px] text-slate-500">~{stats.estimated_reading_time_minutes ?? 0} min read</span>
            </div>
            <div className="card p-4 bg-slate-900/60 border-slate-800">
              <span className="text-xs text-slate-400">Compression</span>
              <p className="text-xl font-bold text-emerald-400 mt-1">
                {stats.summary_to_source_ratio != null ? `${(stats.summary_to_source_ratio * 100).toFixed(0)}%` : '—'}
              </p>
              <span className="text-[11px] text-slate-500">{fmt(stats.summary_word_count)} summary words</span>
            </div>
            <div className="card p-4 bg-slate-900/60 border-slate-800">
              <span className="text-xs text-slate-400">Sections Detected</span>
              <p className="text-xl font-bold text-primary-400 mt-1">
                {a.detected_sections?.length || 0}
              </p>
              <span className="text-[11px] text-slate-500">Heuristic structural map</span>
            </div>
            <div className="card p-4 bg-slate-900/60 border-slate-800">
              <span className="text-xs text-slate-400">Evidence Dimensions</span>
              <p className="text-xl font-bold text-violet-400 mt-1">
                {methFindings.total_found}/{methFindings.total_dimensions}
              </p>
              <span className="text-[11px] text-slate-500">Verified structured leads</span>
            </div>
          </div>

          {/* Executive Synthesis Card */}
          <div className="card p-6 bg-slate-900/70 border-slate-800 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-primary-400" />
                  Executive Summary Brief
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">Top salient sentences extracted via graph PageRank</p>
              </div>
              <button
                onClick={() => setTab('summary')}
                className="text-xs text-primary-400 hover:text-primary-300 font-medium flex items-center gap-1 self-start sm:self-auto"
              >
                Inspect sentence evidence <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap">
              {a.concise_summary || currentSummary || 'No summary available.'}
            </p>
          </div>

          {/* Top Keyphrases Snapshot */}
          {(a.key_phrases || []).length > 0 && (
            <div className="card p-6 bg-slate-900/70 border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Key className="w-4 h-4 text-amber-400" />
                  Core Extracted Key Phrases
                </h3>
                <button
                  onClick={() => setTab('phrases')}
                  className="text-xs text-slate-400 hover:text-slate-300 flex items-center gap-1"
                >
                  View all ({a.key_phrases.length}) <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className="flex flex-wrap gap-2 pt-1">
                {a.key_phrases.slice(0, 10).map((p, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-800/80 text-slate-200 border border-slate-700/60"
                  >
                    <span>{p.phrase}</span>
                    <span className="text-[10px] text-slate-500 font-mono">#{p.rank}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Key Findings Quick Matrix */}
          {methFindings.total_found > 0 && (
            <div className="card p-6 bg-slate-900/70 border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-emerald-400" />
                    Key Research Leads Identified
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">Automated extraction grounded in original passages</p>
                </div>
                <button
                  onClick={() => setTab('methodology')}
                  className="text-xs text-primary-400 hover:text-primary-300 font-medium flex items-center gap-1"
                >
                  Explore full matrix <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                {methFindings.dimensions.filter(d => d.found).slice(0, 4).map((d) => (
                  <div key={d.dimension} className="p-3.5 bg-slate-800/40 rounded-lg border border-slate-800">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-medium text-primary-300">{d.label}</span>
                      {d.section && (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50">
                          {d.section}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">
                      {d.summary}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────── */}
      {/* 2. SUMMARY & SOURCE-LINKED EVIDENCE TAB */}
      {/* ──────────────────────────────────────────────────────────── */}
      {tab === 'summary' && (
        <div className="space-y-6">
          <div className="card p-6 bg-slate-900/80 border-slate-800 space-y-5">
            {/* Controls Bar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
              {/* Length Presets */}
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-400 mr-1">Length:</span>
                {['concise', 'medium', 'detailed'].map(level => (
                  <button
                    key={level}
                    onClick={() => handleLevelChange(level)}
                    className={clsx(
                      'px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all',
                      summaryLevel === level
                        ? 'bg-primary-600 text-white shadow-sm'
                        : 'bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700/60',
                    )}
                  >
                    {level}
                  </button>
                ))}
              </div>

              {/* View Toggle and Copy */}
              <div className="flex items-center gap-2">
                <div className="bg-slate-800/90 p-0.5 rounded-lg flex items-center border border-slate-700/60">
                  <button
                    onClick={() => setSummaryViewMode('interactive')}
                    className={clsx(
                      'px-2.5 py-1 text-xs font-medium rounded-md transition-all',
                      summaryViewMode === 'interactive'
                        ? 'bg-primary-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-slate-200',
                    )}
                  >
                    Evidence Inspector
                  </button>
                  <button
                    onClick={() => setSummaryViewMode('continuous')}
                    className={clsx(
                      'px-2.5 py-1 text-xs font-medium rounded-md transition-all',
                      summaryViewMode === 'continuous'
                        ? 'bg-primary-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-slate-200',
                    )}
                  >
                    Continuous Text
                  </button>
                </div>
                <CopyButton text={currentSummary} />
              </div>
            </div>

            {/* Continuous View */}
            {summaryViewMode === 'continuous' && (
              <div className="space-y-4">
                <p className="text-slate-200 leading-relaxed text-sm sm:text-base whitespace-pre-wrap">
                  {currentSummary || 'No summary generated for this level.'}
                </p>
              </div>
            )}

            {/* Interactive Sentence-by-Sentence Evidence View */}
            {summaryViewMode === 'interactive' && (
              <div className="space-y-5">
                <div className="text-xs text-slate-400 flex items-center justify-between">
                  <span>Click any sentence to inspect its exact section provenance and TextRank salience score:</span>
                  <span className="font-mono text-primary-400">{currentEvidenceList.length} sentences</span>
                </div>

                <div className="space-y-2.5">
                  {currentEvidenceList.length === 0 ? (
                    <p className="text-slate-400 text-sm">{currentSummary}</p>
                  ) : (
                    currentEvidenceList.map((item, idx) => {
                      const isSelected = selectedSentence && selectedSentence.index === item.index
                      return (
                        <div
                          key={idx}
                          onClick={() => {
                            setSelectedSentence(item)
                            if (item.page_number) setPdfPage(item.page_number)
                          }}
                          className={clsx(
                            'p-3.5 rounded-xl border text-sm transition-all cursor-pointer space-y-1.5',
                            isSelected
                              ? 'bg-primary-950/40 border-primary-500/60 shadow-md ring-1 ring-primary-500/30'
                              : 'bg-slate-800/40 border-slate-800 hover:bg-slate-800/80 hover:border-slate-700 text-slate-300',
                          )}
                        >
                          <div className="flex items-center justify-between text-[11px] flex-wrap gap-2">
                            <div className="flex items-center gap-2">
                              <span className={clsx(
                                'font-mono px-2 py-0.5 rounded font-semibold',
                                isSelected ? 'bg-primary-600 text-white' : 'bg-slate-700 text-slate-300',
                              )}>
                                #{idx + 1}
                              </span>
                              <span className="font-medium text-slate-400">
                                Section: <strong className="text-slate-200 font-semibold">{item.section || 'Body'}</strong>
                              </span>
                              <span className="font-mono px-2 py-0.5 rounded text-[10px] bg-slate-900 text-primary-300 border border-slate-700/80">
                                Page {item.page_number || 1}
                              </span>
                            </div>
                            <div className="flex items-center gap-2.5">
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setSelectedSentence(item)
                                  if (item.page_number) setPdfPage(item.page_number)
                                  setSplitView(true)
                                }}
                                className="text-[11px] text-primary-400 hover:text-primary-300 flex items-center gap-1 font-medium bg-primary-950/40 px-2 py-0.5 rounded border border-primary-800/40 hover:bg-primary-900/60 transition-all"
                                title="Scroll PDF Reader to this evidence page"
                              >
                                <Columns className="w-3 h-3" /> View in Reader
                              </button>
                              <span className="text-slate-400 font-mono">
                                Score: {item.score?.toFixed?.(4) ?? item.score}
                              </span>
                            </div>
                          </div>
                          <p className={clsx(
                            'leading-relaxed',
                            isSelected ? 'text-white font-medium' : 'text-slate-200',
                          )}>
                            <CitationPopover
                              text={item.text}
                              references={a.citations?.references || []}
                              inTextCitations={a.citations?.in_text_citations || []}
                              onCitationClick={() => setTab('citations')}
                            />
                          </p>
                        </div>
                      )
                    })
                  )}
                </div>

                {/* Evidence Inspector Card */}
                {selectedSentence && (
                  <div className="card p-5 bg-slate-900 border-primary-500/40 shadow-xl space-y-3 mt-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-wrap gap-2">
                      <div className="flex items-center gap-2">
                        <Quote className="w-4 h-4 text-primary-400" />
                        <h3 className="text-sm font-semibold text-white">Source Evidence Inspector</h3>
                        <span className="text-xs px-2 py-0.5 rounded bg-primary-950 text-primary-300 border border-primary-800/50">
                          {selectedSentence.section || 'Body'}
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/40 font-mono">
                          Page {selectedSentence.page_number || 1}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <button
                          onClick={() => {
                            setSplitView(true)
                            if (selectedSentence.page_number) setPdfPage(selectedSentence.page_number)
                          }}
                          className="btn btn-secondary btn-sm text-xs text-primary-300 hover:text-white flex items-center gap-1 border-primary-700/60"
                        >
                          <Columns className="w-3.5 h-3.5 text-primary-400" /> Open in Split Reader
                        </button>
                        <button
                          onClick={() => setTab('source')}
                          className="btn btn-ghost btn-sm text-xs text-slate-400 hover:text-slate-300 flex items-center gap-1"
                        >
                          <Eye className="w-3.5 h-3.5" /> Jump to Source Preview
                        </button>
                        <CopyButton text={selectedSentence.text} label="Copy Sentence" />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Exact Source Sentence</p>
                      <blockquote className="p-3 bg-slate-950/60 rounded-lg border-l-2 border-primary-500 text-slate-200 text-sm leading-relaxed italic">
                        <CitationPopover
                          text={`"${selectedSentence.text}"`}
                          references={a.citations?.references || []}
                          inTextCitations={a.citations?.in_text_citations || []}
                          onCitationClick={() => setTab('citations')}
                        />
                      </blockquote>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs">
                      <div className="p-2.5 bg-slate-800/50 rounded-lg">
                        <span className="text-slate-500 block mb-0.5">Page Location</span>
                        <span className="font-mono font-medium text-primary-400">Page {selectedSentence.page_number || 1}</span>
                      </div>
                      <div className="p-2.5 bg-slate-800/50 rounded-lg">
                        <span className="text-slate-500 block mb-0.5">Original Sentence Index</span>
                        <span className="font-mono font-medium text-slate-200">Sentence #{selectedSentence.index + 1}</span>
                      </div>
                      <div className="p-2.5 bg-slate-800/50 rounded-lg">
                        <span className="text-slate-500 block mb-0.5">Character Span</span>
                        <span className="font-mono font-medium text-slate-200">
                          {selectedSentence.start_char ?? 0} — {selectedSentence.end_char ?? 0}
                        </span>
                      </div>
                      <div className="p-2.5 bg-slate-800/50 rounded-lg">
                        <span className="text-slate-500 block mb-0.5">TextRank Importance</span>
                        <span className="font-mono font-medium text-emerald-400">
                          {selectedSentence.score?.toFixed?.(4) ?? selectedSentence.score}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Responsible AI Disclaimer */}
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-400 space-y-1">
              <div className="flex items-center gap-1.5 text-slate-300 font-medium">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Extractive Grounding Guarantee</span>
              </div>
              <p>
                All summary sentences are selected verbatim directly from the original paper via unsupervised TextRank.
                No generative hallucination or automated rewriting is applied.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────── */}
      {/* 3. RESEARCH METHODOLOGY & FINDINGS TAB */}
      {/* ──────────────────────────────────────────────────────────── */}
      {tab === 'methodology' && (
        <div className="space-y-6">
          <div className="card p-6 bg-slate-900/80 border-slate-800 space-y-5">
            {/* Header with Counter and Filters */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-emerald-400" />
                  Research Methodology & Empirical Findings
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Structured evidence across 9 standard academic dimensions with verbatim citations
                </p>
              </div>

              {/* Filter Tabs */}
              <div className="flex items-center gap-1.5 bg-slate-800/90 p-1 rounded-lg border border-slate-700/60 self-start sm:self-auto">
                <button
                  onClick={() => setMethodologyFilter('all')}
                  className={clsx(
                    'px-2.5 py-1 text-xs font-medium rounded-md transition-all',
                    methodologyFilter === 'all'
                      ? 'bg-primary-600 text-white'
                      : 'text-slate-400 hover:text-slate-200',
                  )}
                >
                  All ({methFindings.total_dimensions})
                </button>
                <button
                  onClick={() => setMethodologyFilter('found')}
                  className={clsx(
                    'px-2.5 py-1 text-xs font-medium rounded-md transition-all flex items-center gap-1',
                    methodologyFilter === 'found'
                      ? 'bg-emerald-600 text-white'
                      : 'text-slate-400 hover:text-emerald-300',
                  )}
                >
                  <CheckCircle2 className="w-3 h-3" /> Found ({methFindings.total_found})
                </button>
                <button
                  onClick={() => setMethodologyFilter('not_stated')}
                  className={clsx(
                    'px-2.5 py-1 text-xs font-medium rounded-md transition-all flex items-center gap-1',
                    methodologyFilter === 'not_stated'
                      ? 'bg-slate-700 text-white'
                      : 'text-slate-400 hover:text-slate-200',
                  )}
                >
                  <XCircle className="w-3 h-3" /> Not Stated ({methFindings.total_dimensions - methFindings.total_found})
                </button>
              </div>
            </div>

            {/* Quality Safeguard Callout */}
            <div className="p-3.5 bg-emerald-950/20 border border-emerald-800/30 rounded-xl flex items-start gap-2.5 text-xs text-emerald-300">
              <ShieldCheck className="w-4 h-4 flex-shrink-0 mt-0.5 text-emerald-400" />
              <div>
                <strong className="font-semibold text-emerald-200">Evidence Safeguard: </strong>
                Information not explicitly supported by the uploaded document is transparently marked as
                <em> 'Not explicitly stated'</em> to prevent fabricated findings during literature reviews.
              </div>
            </div>

            {/* Grid of 9 Structured Dimensions */}
            <div className="grid grid-cols-1 gap-4">
              {filteredDimensions.map((dim) => (
                <div
                  key={dim.dimension}
                  className={clsx(
                    'p-4 rounded-xl border transition-all space-y-3',
                    dim.found
                      ? 'bg-slate-800/40 border-slate-700/80 hover:border-slate-600 shadow-sm'
                      : 'bg-slate-900/40 border-slate-800/70 opacity-75',
                  )}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {dim.found ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      ) : (
                        <XCircle className="w-4 h-4 text-slate-500 flex-shrink-0" />
                      )}
                      <h3 className="text-sm font-semibold text-white">{dim.label}</h3>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                      {dim.found ? (
                        <>
                          {dim.section && (
                            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-primary-950/60 text-primary-300 border border-primary-800/40">
                              Section: {dim.section}
                            </span>
                          )}
                          <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-slate-800 text-primary-300 border border-slate-700">
                            Page {dim.page_number || 1}
                          </span>
                          <button
                            type="button"
                            onClick={() => {
                              if (dim.page_number) setPdfPage(dim.page_number)
                              setSplitView(true)
                            }}
                            className="text-[10px] text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-medium bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40 hover:bg-emerald-900/60 transition-all"
                            title="Scroll PDF reader to this dimension finding"
                          >
                            <Columns className="w-3 h-3" /> View in Reader
                          </button>
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/50 uppercase">
                            Identified
                          </span>
                        </>
                      ) : (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 uppercase">
                          Not Explicitly Stated
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Summary content */}
                  <p className={clsx(
                    'text-sm leading-relaxed',
                    dim.found ? 'text-slate-200 font-medium' : 'text-slate-500 italic',
                  )}>
                    {dim.summary}
                  </p>

                  {/* Verified evidence quote */}
                  {dim.found && dim.evidence && (
                    <div className="pt-1">
                      <div className="p-3 bg-slate-950/60 rounded-lg border-l-2 border-emerald-500 text-xs text-slate-300 leading-relaxed italic space-y-2">
                        <div className="flex items-center justify-between not-italic">
                          <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
                            <Quote className="w-3 h-3" /> Verbatim Source Excerpt
                          </span>
                          <CopyButton text={dim.evidence} label="Copy Excerpt" />
                        </div>
                        <p>
                          <CitationPopover
                            text={`"${dim.evidence}"`}
                            references={a.citations?.references || []}
                            inTextCitations={a.citations?.in_text_citations || []}
                            onCitationClick={() => setTab('citations')}
                          />
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────── */}
      {/* 4. SECTION-WISE INTELLIGENT SUMMARIES TAB */}
      {/* ──────────────────────────────────────────────────────────── */}
      {tab === 'sections' && (
        <div className="space-y-6">
          <div className="card p-6 bg-slate-900/80 border-slate-800 space-y-5">
            <div className="border-b border-slate-800 pb-3">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-primary-400" />
                Section-Wise Intelligent Summaries
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Extractive synthesis generated individually for each detected section to accelerate targeted reading
              </p>
            </div>

            {(!a.section_summaries || a.section_summaries.length === 0) ? (
              <div className="p-8 text-center bg-slate-950/40 rounded-xl border border-slate-800 space-y-3">
                <Layers className="w-10 h-10 text-slate-600 mx-auto" />
                <h3 className="text-sm font-semibold text-slate-300">No Discrete Sections Detected</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                  This document may have non-standard section headings or be a short unsegmented excerpt.
                  The overall document summary provides the best structural synthesis.
                </p>
                <button onClick={() => setTab('summary')} className="btn btn-secondary btn-sm mt-2">
                  View Overall Summary
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {a.section_summaries.map((sec, idx) => {
                  const isExpanded = expandedSection === idx
                  return (
                    <div
                      key={idx}
                      className="card p-5 bg-slate-800/40 border-slate-700/80 hover:border-slate-600 rounded-xl space-y-3.5 transition-all"
                    >
                      {/* Section Title and Metadata */}
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-md bg-primary-950 text-primary-400 border border-primary-800/60 font-mono text-xs flex items-center justify-center font-bold">
                            {idx + 1}
                          </span>
                          <h3 className="text-base font-bold text-white">{sec.name}</h3>
                        </div>

                        <div className="flex items-center gap-2 text-xs flex-wrap">
                          <span className="font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                            {sec.word_count || 0} words
                          </span>
                          <span className="font-mono text-primary-300 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                            Page {sec.page_number || 1}
                          </span>
                          <button
                            type="button"
                            onClick={() => {
                              if (sec.page_number) setPdfPage(sec.page_number)
                              setSplitView(true)
                            }}
                            className="text-[11px] text-primary-400 hover:text-primary-300 flex items-center gap-1 font-medium bg-primary-950/40 px-2 py-0.5 rounded border border-primary-800/40 hover:bg-primary-900/60 transition-all"
                            title="Scroll PDF reader to this section"
                          >
                            <Columns className="w-3 h-3" /> View in Reader
                          </button>
                        </div>
                      </div>

                      {/* Section Summary Text */}
                      <div className="p-3.5 bg-slate-900/70 rounded-lg border border-slate-800/80">
                        <p className="text-sm text-slate-200 leading-relaxed font-medium">
                          {sec.summary_text || 'No section summary could be extracted.'}
                        </p>
                      </div>

                      {/* Key Sentences Toggle */}
                      {sec.sentences && sec.sentences.length > 0 && (
                        <div>
                          <button
                            onClick={() => setExpandedSection(isExpanded ? null : idx)}
                            className="text-xs font-medium text-primary-400 hover:text-primary-300 flex items-center gap-1.5 transition-all"
                          >
                            {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                            {isExpanded ? 'Hide Key Sentences' : `Show ${sec.sentences.length} Key Sentences & Scores`}
                          </button>

                          {isExpanded && (
                            <div className="mt-2.5 space-y-2 pl-3 border-l-2 border-primary-500/50">
                              {sec.sentences.map((sent, sIdx) => (
                                <div key={sIdx} className="text-xs text-slate-300 space-y-1">
                                  <div className="flex items-center gap-2 text-[10px] text-slate-500">
                                    <span className="font-mono">Sentence #{sent.index + 1}</span>
                                    <span>•</span>
                                    <span className="font-mono text-emerald-400">Score: {sent.score}</span>
                                  </div>
                                  <p className="italic text-slate-300 leading-relaxed">"{sent.text}"</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────── */}
      {/* 5. CITATIONS & BIBTEX EXPORTER TAB */}
      {/* ──────────────────────────────────────────────────────────── */}
      {tab === 'citations' && (
        <CitationsPanel citations={a.citations || {}} paperTitle={a.title} />
      )}

      {/* ──────────────────────────────────────────────────────────── */}
      {/* 6. KEY PHRASES TAB */}
      {/* ──────────────────────────────────────────────────────────── */}
      {tab === 'phrases' && (
        <div className="card p-6 bg-slate-900/80 border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Key className="w-4 h-4 text-amber-400" />
                Ranked Key Phrases (YAKE)
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Unsupervised statistical keyphrase extraction scoring 1- to 3-gram domain phrases
              </p>
            </div>
            <CopyButton text={(a.key_phrases || []).map(p => p.phrase).join(', ')} label="Copy All" />
          </div>

          {(a.key_phrases || []).length === 0 ? (
            <p className="text-slate-500 text-sm">No key phrases extracted.</p>
          ) : (
            <div className="space-y-2 pt-2">
              {a.key_phrases.map(p => (
                <div key={p.rank} className="flex items-center gap-3 p-3 bg-slate-800/40 hover:bg-slate-800/70 border border-slate-800 rounded-lg transition-all">
                  <span className="text-xs text-slate-500 w-6 font-mono text-right font-semibold">#{p.rank}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-200 truncate">{p.phrase}</p>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <div className="w-24 h-1.5 bg-slate-700 rounded-full overflow-hidden hidden sm:block">
                      <div
                        className="h-full bg-primary-500 rounded-full"
                        style={{ width: `${Math.round(p.score * 100)}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono text-slate-400 w-12 text-right">{p.score.toFixed(3)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────── */}
      {/* 6. STATISTICS TAB */}
      {/* ──────────────────────────────────────────────────────────── */}
      {tab === 'stats' && (
        <div className="card p-6 bg-slate-900/80 border-slate-800 space-y-5">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-primary-400" />
              Document & Analysis Metrics
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">Quantitative counts and compression statistics</p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              ['Words',              fmt(stats.word_count)],
              ['Characters',         fmt(stats.character_count)],
              ['Sentences',          fmt(stats.sentence_count)],
              ['Paragraphs',         fmt(stats.paragraph_count)],
              ['Reading Time',       `${stats.estimated_reading_time_minutes ?? '—'} min`],
              ['WPM Assumption',     `${stats.words_per_minute_assumption ?? 200} wpm`],
              ['Summary Words',      fmt(stats.summary_word_count)],
              ['Compression Ratio',  stats.summary_to_source_ratio != null
                ? `${(stats.summary_to_source_ratio * 100).toFixed(1)}%` : '—'],
            ].map(([label, value]) => (
              <div key={label} className="bg-slate-800/40 border border-slate-800 rounded-xl p-3.5">
                <p className="text-xs text-slate-500 mb-1">{label}</p>
                <p className="text-lg font-bold text-white font-mono">{value}</p>
              </div>
            ))}
          </div>

          <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800 text-xs text-slate-400 space-y-1">
            <span className="font-semibold text-slate-300">Methodology Note:</span>
            <p>
              Estimated reading time assumes standard scientific reading speed of {stats.words_per_minute_assumption ?? 200} words per minute.
              Compression ratio represents summary length relative to source length.
            </p>
          </div>
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────── */}
      {/* 7. SOURCE TEXT PREVIEW TAB */}
      {/* ──────────────────────────────────────────────────────────── */}
      {tab === 'source' && (
        <div className="card p-6 bg-slate-900/80 border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary-400" />
                Preprocessed Source Text Preview
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Cleaned academic text passed into the NLP algorithms
              </p>
            </div>
            <CopyButton text={a.source_text_preview || ''} label="Copy Preview" />
          </div>

          <div className="bg-slate-950/80 rounded-xl p-4 text-xs sm:text-sm text-slate-300 leading-relaxed font-mono whitespace-pre-wrap max-h-96 overflow-y-auto scrollbar-thin border border-slate-800">
            {a.source_text_preview || 'Source preview not available.'}
          </div>
        </div>
      )}
        </div>
      </div>
    </div>
  )
}
