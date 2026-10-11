// src/pages/UploadPage.jsx
// ──────────────────────────
// Upload PDF or paste text for analysis.

import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import {
  AlertCircle, CheckCircle, FileText, Loader2,
  Type, Upload, X,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { analysesApi, documentsApi } from '../services/api'
import clsx from 'clsx'

const SUMMARY_TYPES = [
  { value: 'concise',  label: 'Concise',  desc: 'Brief overview (~15% of sentences)' },
  { value: 'medium',   label: 'Medium',   desc: 'Balanced summary (~30% of sentences)' },
  { value: 'detailed', label: 'Detailed', desc: 'Comprehensive (~50% of sentences)' },
]

const MAX_BYTES = 20 * 1024 * 1024  // 20 MB

export default function UploadPage() {
  const navigate = useNavigate()
  const [mode,        setMode]        = useState('pdf')   // 'pdf' | 'text'
  const [file,        setFile]        = useState(null)
  const [text,        setText]        = useState('')
  const [title,       setTitle]       = useState('')
  const [summaryType, setSummaryType] = useState('medium')
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState(null)
  const [progress,    setProgress]    = useState('')

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

  const handleSubmit = async (ev) => {
    ev.preventDefault()
    setError(null)

    // Validate
    if (!title.trim()) { setError('Please enter a document title.'); return }
    if (mode === 'pdf' && !file) { setError('Please select a PDF file.'); return }
    if (mode === 'text' && text.trim().length < 50) {
      setError('Please paste at least 50 characters of text.'); return
    }

    setLoading(true)
    try {
      let analysisId

      if (mode === 'pdf') {
        // Step 1: upload
        setProgress('Uploading PDF…')
        const fd = new FormData()
        fd.append('file', file)
        fd.append('title', title.trim())
        const uploadRes = await documentsApi.upload(fd)
        const docId = uploadRes.data._id

        // Step 2: analyse
        setProgress('Running NLP analysis…')
        const analysisRes = await analysesApi.analyzeDocument(docId, { summary_type: summaryType })
        analysisId = analysisRes.data._id
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
        <p className="text-slate-400 text-sm mt-1">Upload a PDF or paste text to get summaries and key phrases.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Mode toggle */}
        <div className="card p-1 flex gap-1">
          {[
            { v: 'pdf',  icon: Upload, label: 'Upload PDF' },
            { v: 'text', icon: Type,   label: 'Paste Text' },
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

        {/* Title */}
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

        {/* PDF upload */}
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

        {/* Text paste */}
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

        {/* Error */}
        {error && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-red-900/30 border border-red-800/50 text-red-300 text-sm">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            {error}
          </div>
        )}

        {/* Submit */}
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
              Run Analysis
            </>
          )}
        </button>

        <p className="text-xs text-slate-500 text-center leading-relaxed">
          Results are generated by automated NLP algorithms. Please review the original
          document before relying on or citing these outputs.
        </p>
      </form>
    </div>
  )
}
