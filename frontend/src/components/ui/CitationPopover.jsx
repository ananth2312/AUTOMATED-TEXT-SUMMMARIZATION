// src/components/ui/CitationPopover.jsx
// ─────────────────────────────────────
// Inline citation highlighter and hover popover component.
// Detects [1], [2, 3], and (Author et al., 2020) and shows bibliography details on hover.

import { useState } from 'react'
import { ExternalLink, Quote } from 'lucide-react'
import clsx from 'clsx'

export default function CitationPopover({
  text = '',
  references = [],
  inTextCitations = [],
  onCitationClick,
}) {
  if (!text) return null

  // Regex for numeric citations [1], [1, 2] and author-year citations (Vaswani et al., 2017)
  const citationRegex = /(\[\d+(?:,\s*\d+)*\]|\([A-Z][a-zA-Z\s]+(?:et al\.)?,\s*\d{4}\))/g

  const parts = []
  let lastIndex = 0
  let match

  while ((match = citationRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({
        type: 'text',
        content: text.slice(lastIndex, match.index),
      })
    }

    const matchStr = match[0]
    let ref = null

    // Numeric match e.g. [1]
    const numMatch = matchStr.match(/\d+/)
    if (numMatch) {
      const id = parseInt(numMatch[0], 10)
      ref = references.find(r => r.id === id)
    }

    // Author-year fallback
    if (!ref && inTextCitations && inTextCitations.length > 0) {
      const found = inTextCitations.find(c => c.match === matchStr)
      if (found && found.ref_id) {
        ref = references.find(r => r.id === found.ref_id)
      }
    }

    parts.push({
      type: 'citation',
      content: matchStr,
      reference: ref,
    })

    lastIndex = match.index + matchStr.length
  }

  if (lastIndex < text.length) {
    parts.push({
      type: 'text',
      content: text.slice(lastIndex),
    })
  }

  return (
    <span>
      {parts.map((p, i) => {
        if (p.type === 'text') {
          return <span key={i}>{p.content}</span>
        }

        const ref = p.reference

        return (
          <span
            key={i}
            className="relative group inline-block mx-0.5 align-baseline"
          >
            <span
              onClick={(e) => {
                e.stopPropagation()
                if (onCitationClick && ref) onCitationClick(ref)
              }}
              className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-primary-950/80 text-primary-300 border border-primary-700/60 hover:bg-primary-900 hover:text-white cursor-pointer transition-all shadow-sm"
              title="Hover to view bibliography entry"
            >
              {p.content}
            </span>

            {/* Hover Popover */}
            <span
              className="pointer-events-none group-hover:pointer-events-auto opacity-0 group-hover:opacity-100 transition-opacity duration-150 absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-3 bg-slate-900/95 backdrop-blur-md border border-slate-700 rounded-xl shadow-2xl text-left z-50 block"
            >
              <span className="flex items-center justify-between border-b border-slate-800 pb-1.5 mb-1.5">
                <span className="flex items-center gap-1.5 text-xs font-bold text-primary-400">
                  <Quote className="w-3.5 h-3.5" />
                  {ref?.id ? `Reference [${ref.id}]` : 'Citation Preview'}
                </span>
                {ref?.year && (
                  <span className="text-[10px] font-mono bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">
                    {ref.year}
                  </span>
                )}
              </span>

              {ref ? (
                <span className="block space-y-1 text-xs">
                  <span className="font-semibold text-slate-100 block leading-snug line-clamp-2">
                    {ref.title || 'Untitled Work'}
                  </span>
                  <span className="text-slate-400 text-[11px] block truncate">
                    {ref.authors?.length > 0 ? ref.authors.join(', ') : 'Authors not listed'}
                  </span>
                  {ref.venue && (
                    <span className="text-slate-500 text-[10px] block italic truncate">
                      {ref.venue}
                    </span>
                  )}
                  {ref.doi && (
                    <a
                      href={`https://doi.org/${ref.doi}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-primary-400 hover:text-primary-300 text-[10px] inline-flex items-center gap-1 mt-1 font-mono"
                    >
                      doi:{ref.doi} <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  )}
                </span>
              ) : (
                <span className="text-xs text-slate-400 block italic">
                  Citation marker detected in text. View bibliography tab for all parsed entries.
                </span>
              )}
            </span>
          </span>
        )
      })}
    </span>
  )
}
