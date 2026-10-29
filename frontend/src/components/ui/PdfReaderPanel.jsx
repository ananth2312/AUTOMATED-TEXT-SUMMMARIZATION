// src/components/ui/PdfReaderPanel.jsx
// ────────────────────────────────────
// Split-Screen Interactive PDF Reader with bidirectional evidence sync.
// Displays the original PDF document side-by-side with NLP analysis.

import { useEffect, useRef, useState } from 'react'
import {
  ChevronLeft, ChevronRight, ExternalLink, FileText,
  Loader2, Maximize2, Sparkles, AlertCircle, RefreshCw,
} from 'lucide-react'
import { documentsApi } from '../../services/api'
import clsx from 'clsx'

export default function PdfReaderPanel({
  documentId,
  pageCount = 1,
  targetPage = 1,
  syncedSentence = null,
  sourceText = '',
}) {
  const [pdfUrl, setPdfUrl] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(targetPage || 1)
  const [inputPage, setInputPage] = useState(String(targetPage || 1))
  const [totalEstimatedPages, setTotalEstimatedPages] = useState(pageCount || 1)
  const iframeRef = useRef(null)

  // Sync when targetPage changes from parent (e.g., clicking evidence sentence)
  useEffect(() => {
    if (targetPage && targetPage !== currentPage) {
      setCurrentPage(targetPage)
      setInputPage(String(targetPage))
    }
  }, [targetPage])

  // Fetch the PDF blob with Authorization token
  useEffect(() => {
    if (!documentId) {
      setLoading(false)
      return
    }

    let active = true
    let blobUrl = null

    setLoading(true)
    setError(null)

    documentsApi.getPdfBlob(documentId)
      .then(res => {
        if (!active) return
        const blob = new Blob([res.data], { type: 'application/pdf' })
        blobUrl = URL.createObjectURL(blob)
        setPdfUrl(blobUrl)
        setLoading(false)
      })
      .catch(err => {
        if (!active) return
        setError(err.response?.data?.detail || 'Failed to load PDF file.')
        setLoading(false)
      })

    return () => {
      active = false
      if (blobUrl) URL.revokeObjectURL(blobUrl)
    }
  }, [documentId])

  const handlePageJump = (page) => {
    const p = Math.max(1, Math.min(page, Math.max(pageCount, 100)))
    setCurrentPage(p)
    setInputPage(String(p))
  }

  const handleInputChange = (e) => {
    setInputPage(e.target.value)
  }

  const handleInputKeyDown = (e) => {
    if (e.key === 'Enter') {
      const p = parseInt(inputPage, 10)
      if (!isNaN(p)) {
        handlePageJump(p)
      }
    }
  }

  return (
    <div className="card p-0 overflow-hidden bg-slate-900 border-slate-700/80 flex flex-col h-[750px] shadow-xl animate-fade-in">
      {/* Top Controls Toolbar */}
      <div className="bg-slate-800/95 border-b border-slate-700/80 px-4 py-2.5 flex items-center justify-between gap-3 text-xs flex-wrap">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-primary-400" />
          <span className="font-semibold text-white">Interactive PDF Reader</span>
          {syncedSentence && (
            <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              <Sparkles className="w-3 h-3" />
              Page {currentPage} Synced
            </span>
          )}
        </div>

        {/* Page navigation controls */}
        {documentId && (
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => handlePageJump(currentPage - 1)}
              disabled={currentPage <= 1}
              className="btn btn-ghost btn-sm p-1 text-slate-300 hover:text-white disabled:opacity-30"
              title="Previous Page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-1 font-mono text-slate-300 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-700">
              <span>Page</span>
              <input
                type="text"
                value={inputPage}
                onChange={handleInputChange}
                onKeyDown={handleInputKeyDown}
                className="w-8 text-center bg-transparent border-0 text-white font-bold p-0 focus:outline-none focus:ring-1 focus:ring-primary-500 rounded"
              />
              {pageCount > 0 && <span className="text-slate-500">/ {pageCount}</span>}
            </div>

            <button
              onClick={() => handlePageJump(currentPage + 1)}
              disabled={pageCount > 0 && currentPage >= pageCount}
              className="btn btn-ghost btn-sm p-1 text-slate-300 hover:text-white disabled:opacity-30"
              title="Next Page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>

            {pdfUrl && (
              <a
                href={pdfUrl}
                target="_blank"
                rel="noreferrer"
                className="btn btn-ghost btn-sm p-1 text-slate-400 hover:text-primary-300 ml-1"
                title="Open PDF in new browser tab"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
        )}
      </div>

      {/* Reader Body */}
      <div className="flex-1 relative bg-slate-950 flex flex-col items-center justify-center overflow-hidden">
        {loading && (
          <div className="flex flex-col items-center gap-3 p-8 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
            <p className="text-sm">Loading PDF stream...</p>
          </div>
        )}

        {error && (
          <div className="p-6 text-center max-w-sm space-y-3">
            <AlertCircle className="w-8 h-8 text-amber-400 mx-auto" />
            <p className="text-sm text-slate-300 font-medium">{error}</p>
            <p className="text-xs text-slate-500">
              The PDF may be processed locally or stored as plain text. You can still inspect full evidence in the tabs.
            </p>
          </div>
        )}

        {/* PDF viewer iframe */}
        {!loading && !error && pdfUrl && (
          <iframe
            ref={iframeRef}
            src={`${pdfUrl}#page=${currentPage}&zoom=page-width&navpanes=0`}
            title="PDF Document Viewer"
            className="w-full h-full border-0"
          />
        )}

        {/* Fallback for text-only analyses */}
        {!loading && !error && !documentId && (
          <div className="p-6 h-full w-full overflow-y-auto space-y-3 text-slate-300 text-xs sm:text-sm font-mono leading-relaxed">
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-slate-400 text-xs mb-2">
              <span className="font-semibold text-slate-300">Text Ingestion Mode:</span> This analysis was performed on pasted text. Full text is rendered below with evidence highlighting.
            </div>
            <p className="whitespace-pre-wrap">{sourceText || 'No source text available.'}</p>
          </div>
        )}
      </div>

      {/* Synced Sentence Bottom Banner */}
      {syncedSentence && (
        <div className="bg-slate-900 border-t border-slate-800 px-4 py-2 flex items-center justify-between text-xs text-slate-300">
          <div className="flex items-center gap-2 truncate pr-2">
            <span className="text-primary-400 font-semibold flex-shrink-0">Selected Sentence:</span>
            <span className="italic truncate text-slate-300">"{syncedSentence.text}"</span>
          </div>
          <span className="text-slate-500 font-mono text-[11px] flex-shrink-0">
            Page {syncedSentence.page_number || currentPage}
          </span>
        </div>
      )}
    </div>
  )
}
