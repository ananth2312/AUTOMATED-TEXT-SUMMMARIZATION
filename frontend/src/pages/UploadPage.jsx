// src/pages/UploadPage.jsx
// ──────────────────────────
// Upload PDF, import via arXiv/DOI, or paste text for analysis.

import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import {
  AlertCircle, BookMarked, CheckCircle, ExternalLink, FileText,
  Globe, Info, Loader2, Sparkles, Type, Upload, X,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { analysesApi, documentsApi } from '../services/api'
import clsx from 'clsx'

const SUMMARY_TYPES = [
  { value: 'concise',  label: 'Concise',  desc: 'Brief overview (~15% of sentences)' },
  { value: 'medium',   label: 'Medium',   desc: 'Balanced summary (~30% of sentences)' },
  { value: 'detailed', label: 'Detailed', desc: 'Comprehensive (~50% of sentences)' },
]

const SAMPLE_PAPERS = [
  { label: 'Attention Is All You Need', id: '1706.03762' },
  { label: 'BERT (Devlin et al.)', id: '1810.04805' },
  { label: 'LoRA (Hu et al.)', id: '2106.09685' },
]

const MAX_BYTES = 20 * 1024 * 1024  // 20 MB

export default function UploadPage() {
  const navigate = useNavigate()
  const [mode,            setMode]            = useState('pdf')   // 'pdf' | 'arxiv' | 'text'
  const [file,            setFile]            = useState(null)
  const [externalInput,   setExternalInput]   = useState('')
  const [previewMeta,     setPreviewMeta]     = useState(null)
  const [previewLoading,  setPreviewLoading]  = useState(false)
  const [text,            setText]            = useState('')
  const [title,           setTitle]           = useState('')
  const [summaryType,     setSummaryType]     = useState('medium')
  const [loading,         setLoading]         = useState(false)
  const [error,           setError]           = useState(null)
  const [progress,        setProgress]        = useState('')

  const onDrop = useCallback(accepted => {
    const f = accepted[0]
    if (!f) return
    if (!f.name.toLowerCase().endsWith('.pdf')) {
      toast.error('Only PDF files are supported.'); return
    }
    if (f.size > MAX_BYTES) {
      toast.error('File exceeds the 20 MB limit.'); return
    }
    setFile(f)
    if (!title) setTitle(f.name.replace(/\.pdf$/i, ''))
    setError(null)
  }, [title])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'application/pdf': ['.pdf'] }, maxFiles: 1,
  })

  // Pre-fetch metadata for arXiv or DOI
  const handleFetchPreview = async (overrideInput) => {
    const target = (overrideInput || externalInput).trim()
    if (!target) {
      toast.error('Please enter an arXiv ID or DOI first.')
      return
    }
    setPreviewLoading(true)
    setError(null)
    try {
      const res = await documentsApi.previewExternal({ url_or_identifier: target })
      setPreviewMeta(res.data)
      if (res.data.title && !title) {
        setTitle(res.data.title)
      }
      toast.success('Metadata fetched successfully!')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Could not fetch metadata for this identifier.'
      setError(msg)
      toast.error(msg)
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleSelectSample = (sampleId) => {
    setExternalInput(sampleId)
    handleFetchPreview(sampleId)
  }

  const handleSubmit = async (ev) => {
    ev.preventDefault()
    setError(null)

    // Validate
    if (mode === 'pdf') {
      if (!file) { setError('Please select a PDF file.'); return }
      if (!title.trim()) { setError('Please enter a document title.'); return }
    } else if (mode === 'arxiv') {
      if (!externalInput.trim()) { setError('Please enter an arXiv ID, URL, or DOI.'); return }
    } else if (mode === 'text') {
      if (!title.trim()) { setError('Please enter a document title.'); return }
      if (text.trim().length < 50) {
        setError('Please paste at least 50 characters of text.'); return
      }
    }

    setLoading(true)
    try {
      let analysisId

      if (mode === 'pdf') {
        setProgress('Uploading PDF…')
        const fd = new FormData()
        fd.append('file', file)
        fd.append('title', title.trim())
        const uploadRes = await documentsApi.upload(fd)
        const docId = uploadRes.data._id

        setProgress('Running NLP analysis…')
        const analysisRes = await analysesApi.analyzeDocument(docId, { summary_type: summaryType })
        analysisId = analysisRes.data._id
      } else if (mode === 'arxiv') {
        setProgress('Importing metadata & downloading PDF…')
        const res = await documentsApi.importExternal({
          url_or_identifier: externalInput.trim(),
          summary_type: summaryType,
          auto_analyze: true,
        })
        analysisId = res.data.analysis_id
      } else {
        setProgress('Running NLP analysis…')
        const res = await analysesApi.analyzeText({
          title: title.trim(),
          text: text.trim(),
          summary_type: summaryType,
        })
        analysisId = res.data._id
      }

      toast.success('Analysis complete!')
      navigate(`/analyses/${analysisId}`)
    } catch (err) {
      const msg = err.response?.data?.detail || 'Analysis failed. Please try again.'
      setError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
      setProgress('')
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Analyse a Research Paper</h1>
        <p className="text-slate-400 text-sm mt-1">
          Upload a PDF, import directly via arXiv / DOI, or paste academic text for automated intelligence.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Mode toggle */}
        <div className="card p-1 flex gap-1">
          {[
            { v: 'pdf',   icon: Upload, label: 'Upload PDF' },
            { v: 'arxiv', icon: Globe,  label: 'arXiv / DOI' },
            { v: 'text',  icon: Type,   label: 'Paste Text' },
          ].map(({ v, icon: Icon, label }) => (
            <button
              key={v}
              type="button"
              onClick={() => { setMode(v); setError(null) }}
              className={clsx(
                'flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-all',
                mode === v
                  ? 'bg-primary-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800',
              )}
            >
              <Icon className="w-4 h-4" /> {label}
            </button>
          ))}
        </div>

        {/* Title (for PDF and Text mode, or optional override in arXiv mode) */}
        {mode !== 'arxiv' && (
          <div>
            <label className="label" htmlFor="doc-title">Document Title</label>
            <input
              id="doc-title"
              type="text"
              className="input"
              placeholder="e.g. Attention Is All You Need"
              value={title}
              onChange={e => setTitle(e.target.value)}
              maxLength={300}
            />
          </div>
        )}

        {/* PDF upload mode */}
        {mode === 'pdf' && (
          <div>
            <label className="label">PDF File <span className="text-slate-500 font-normal">(max 20 MB)</span></label>
            {file ? (
              <div className="card p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary-900/40 flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5 text-primary-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-200 truncate">{file.name}</p>
                  <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
                <button type="button" onClick={() => setFile(null)} className="btn-ghost p-1 rounded">
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div
                {...getRootProps()}
                className={clsx(
                  'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all',
                  isDragActive
                    ? 'border-primary-500 bg-primary-900/20'
                    : 'border-slate-700 hover:border-slate-600 hover:bg-slate-800/30',
                )}
              >
                <input {...getInputProps()} id="pdf-upload" />
                <Upload className={clsx('w-10 h-10 mx-auto mb-3', isDragActive ? 'text-primary-400' : 'text-slate-500')} />
                <p className="text-sm text-slate-300 font-medium">
                  {isDragActive ? 'Drop your PDF here' : 'Drag & drop a PDF, or click to browse'}
                </p>
                <p className="text-xs text-slate-500 mt-1">PDF only · Maximum 20 MB</p>
              </div>
            )}
          </div>
        )}

        {/* Direct arXiv / DOI mode */}
        {mode === 'arxiv' && (
          <div className="space-y-4">
            <div>
              <label className="label" htmlFor="arxiv-input">
                arXiv ID, arXiv URL, or DOI
              </label>
              <div className="flex gap-2">
                <input
                  id="arxiv-input"
                  type="text"
                  className="input flex-1 font-mono text-sm"
                  placeholder="e.g. 1706.03762 or 10.1145/3318464.3389700"
                  value={externalInput}
                  onChange={e => setExternalInput(e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => handleFetchPreview()}
                  disabled={previewLoading || !externalInput.trim()}
                  className="btn btn-secondary flex items-center gap-1.5 whitespace-nowrap"
                >
                  {previewLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4 text-primary-400" />}
                  Fetch Info
                </button>
              </div>

              {/* Preset quick samples */}
              <div className="flex flex-wrap items-center gap-1.5 mt-2">
                <span className="text-xs text-slate-500">Quick examples:</span>
                {SAMPLE_PAPERS.map(s => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => handleSelectSample(s.id)}
                    className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-0.5 rounded border border-slate-700 transition-colors"
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Live Paper Preview Card */}
            {previewMeta && (
              <div className="card p-4 bg-slate-800/60 border-slate-700 space-y-3 animate-fade-in">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-primary-900/60 text-primary-300 border border-primary-700/50 mb-1.5">
                      <BookMarked className="w-3 h-3" />
                      {previewMeta.source.toUpperCase()} · {previewMeta.identifier}
                    </span>
                    <h3 className="text-base font-semibold text-white leading-snug">
                      {previewMeta.title}
                    </h3>
                  </div>
                </div>

                <div className="text-xs text-slate-400 space-y-1">
                  {previewMeta.authors?.length > 0 && (
                    <p><span className="text-slate-500">Authors:</span> {previewMeta.authors.slice(0, 4).join(', ')}{previewMeta.authors.length > 4 ? ' et al.' : ''}</p>
                  )}
                  <div className="flex gap-4 text-slate-500">
                    {previewMeta.year && <span>Year: <strong className="text-slate-300">{previewMeta.year}</strong></span>}
                    {previewMeta.venue && <span>Venue: <strong className="text-slate-300">{previewMeta.venue}</strong></span>}
                  </div>
                </div>

                {previewMeta.abstract && (
                  <div className="text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 max-h-28 overflow-y-auto leading-relaxed">
                    <p className="text-slate-500 font-medium mb-1">Abstract:</p>
                    {previewMeta.abstract}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Text paste mode */}
        {mode === 'text' && (
          <div>
            <label className="label" htmlFor="paste-text">
              Academic Text <span className="text-slate-500 font-normal">(minimum 50 characters)</span>
            </label>
            <textarea
              id="paste-text"
              className="input min-h-[200px] resize-y"
              placeholder="Paste your research paper text here…"
              value={text}
              onChange={e => setText(e.target.value)}
            />
            <p className="text-xs text-slate-500 mt-1">{text.length} characters</p>
          </div>
        )}

        {/* Summary type */}
        <div>
          <label className="label">Summary Length</label>
          <div className="grid grid-cols-3 gap-3">
            {SUMMARY_TYPES.map(({ value, label, desc }) => (
              <label key={value} className={clsx(
                'card p-3 cursor-pointer transition-all',
                summaryType === value ? 'border-primary-600 bg-primary-900/20' : 'hover:border-slate-700',
              )}>
                <input
                  type="radio"
                  name="summary_type"
                  value={value}
                  checked={summaryType === value}
                  onChange={() => setSummaryType(value)}
                  className="sr-only"
                />
                <p className="text-sm font-medium text-slate-200">{label}</p>
                <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{desc}</p>
              </label>
            ))}
          </div>
        </div>

        {/* Error notification */}
        {error && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-red-900/30 border border-red-800/50 text-red-300 text-sm">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            {error}
          </div>
        )}

        {/* Submit Button */}
        <button
          id="analyse-submit"
          type="submit"
          disabled={loading}
          className="btn btn-primary w-full btn-lg"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              {progress || 'Processing…'}
            </>
          ) : (
            <>
              <CheckCircle className="w-4 h-4" />
              {mode === 'arxiv' ? 'Import & Run Analysis' : 'Run Analysis'}
            </>
          )}
        </button>

        <p className="text-xs text-slate-500 text-center leading-relaxed">
          Extractive summaries and methodology findings are grounded directly in the paper's source text.
        </p>
      </form>
    </div>
  )
}
