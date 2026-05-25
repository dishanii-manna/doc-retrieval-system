import { useState, useEffect, useRef } from 'react'
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Download, X, AlertCircle } from 'lucide-react'
import { getPdfPageUrl, getPdfInfo } from '../services/api'

export default function PdfViewer({ docId, initialPage, highlightText, matchedText, onClose }) {
  const [page, setPage] = useState(initialPage || 1)
  const [zoom, setZoom] = useState(0.75)
  const [totalPages, setTotalPages] = useState(null)
  const [loading, setLoading] = useState(true)
  const [imgError, setImgError] = useState(false)

  const [activeHighlight, setActiveHighlight] = useState(highlightText || '')
  const [activeMatchedText, setActiveMatchedText] = useState(matchedText || '')
  const matchOriginRef = useRef({ docId, page: initialPage || 1 })

  useEffect(() => {
    setPage(initialPage || 1)
    setActiveHighlight(highlightText || '')
    setActiveMatchedText(matchedText || '')
    matchOriginRef.current = { docId, page: initialPage || 1 }
  }, [initialPage, docId, highlightText, matchedText])

  useEffect(() => {
    getPdfInfo(docId)
      .then(info => setTotalPages(info.page_count))
      .catch(() => setTotalPages(null))
  }, [docId])

  const isOnOriginPage =
    page === matchOriginRef.current.page && docId === matchOriginRef.current.docId

  const src = getPdfPageUrl(docId, page, zoom, isOnOriginPage ? activeHighlight : '')

  const goTo = (p) => {
    const clamped = totalPages ? Math.max(1, Math.min(p, totalPages)) : Math.max(1, p)
    setPage(clamped)
  }

  const highlightExcerpt = (text, keyword) => {
    if (!text || !keyword) return text
    const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp('(' + escaped + ')', 'gi')
    return text.replace(regex, '<mark style="background:gold;padding:0 2px;border-radius:2px;">$1</mark>')
  }

  return (
    <div className="flex flex-col h-full bg-stone-100 rounded-xl overflow-hidden">

      {/* Toolbar */}
      <div className="flex items-center gap-2 px-4 py-2 bg-stone-800 text-white text-sm shrink-0">
        <span className="font-medium truncate flex-1">{docId}.pdf</span>

        <button onClick={() => goTo(page - 1)} disabled={page <= 1}
          className="p-1 rounded hover:bg-stone-700 disabled:opacity-30">
          <ChevronLeft size={18} />
        </button>

        <span className="flex items-center gap-1">
          <input
            type="number" value={page} min={1} max={totalPages || 9999}
            onChange={e => goTo(Number(e.target.value))}
            className="w-12 text-center bg-stone-700 rounded px-1 py-0.5"
          />
          {totalPages && <span className="text-stone-400">/ {totalPages}</span>}
        </span>

        <button onClick={() => goTo(page + 1)} disabled={totalPages && page >= totalPages}
          className="p-1 rounded hover:bg-stone-700 disabled:opacity-30">
          <ChevronRight size={18} />
        </button>

        <div className="flex items-center gap-1 border-l border-stone-600 ml-2 pl-2">
          <button onClick={() => setZoom(z => Math.max(0.5, +(z - 0.25).toFixed(2)))}
            className="p-1 rounded hover:bg-stone-700"><ZoomOut size={16} /></button>
          <span className="w-10 text-center">{Math.round(zoom * 100)}%</span>
          <button onClick={() => setZoom(z => Math.min(4, +(z + 0.25).toFixed(2)))}
            className="p-1 rounded hover:bg-stone-700"><ZoomIn size={16} /></button>
        </div>

        {activeHighlight && isOnOriginPage && (
          <div className="flex items-center gap-1 border-l border-stone-600 ml-2 pl-2">
            <span className="text-xs bg-yellow-400 text-stone-800 px-2 py-0.5 rounded font-medium">
              Highlighted
            </span>
          </div>
        )}

        <a href={`/api/pdf/${docId}/download`} download
          className="p-1 rounded hover:bg-stone-700 ml-1">
          <Download size={16} />
        </a>
        {onClose && (
          <button onClick={onClose} className="p-1 rounded hover:bg-stone-700 ml-1">
            <X size={16} />
          </button>
        )}
      </div>

      {/* Match banner */}
      {activeHighlight && isOnOriginPage && (
        <div className="shrink-0 flex items-center gap-2 bg-yellow-300 px-3 py-1.5 text-stone-800 text-xs font-semibold">
          Match found — "{activeHighlight}" appears on this page
        </div>
      )}

      {activeHighlight && !isOnOriginPage && (
        <div className="shrink-0 flex items-center gap-2 bg-stone-600 px-3 py-1.5 text-white text-xs font-semibold">
          <AlertCircle size={14} className="shrink-0" />
          Match is on page {matchOriginRef.current.page} —
          <button onClick={() => goTo(matchOriginRef.current.page)}
            className="underline ml-1 hover:text-yellow-300 transition-colors">
            Go back
          </button>
        </div>
      )}

      {/* PDF Image Area - scrollable */}
      <div className="flex-1 overflow-auto flex items-start justify-center p-4">
        {loading && (
          <div className="flex items-center justify-center w-full h-full">
            <div className="w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {imgError && (
          <div className="flex flex-col items-center justify-center w-64 h-96 text-stone-400 gap-2">
            <AlertCircle size={32} />
            <span className="text-sm">Could not load page {page}</span>
          </div>
        )}

        <img
          key={`${docId}-${page}-${zoom}-${isOnOriginPage ? activeHighlight : ''}`}
          src={src}
          alt={`Page ${page}`}
          onLoad={() => { setLoading(false); setImgError(false) }}
          onLoadStart={() => { setLoading(true); setImgError(false) }}
          onError={() => { setLoading(false); setImgError(true) }}
          className="shadow-xl max-w-none rounded"
          style={{ display: (loading || imgError) ? 'none' : 'block' }}
        />
      </div>

      {/* Matched excerpt - below PDF, fixed height */}
      {activeHighlight && isOnOriginPage && activeMatchedText && (
        <div className="shrink-0 border-t border-stone-200 bg-yellow-50 px-4 py-2 max-h-28 overflow-auto">
          <div className="text-xs text-yellow-700 font-semibold mb-1">Matched excerpt:</div>
          <div className="text-xs text-stone-700 leading-relaxed"
            dangerouslySetInnerHTML={{ __html: highlightExcerpt(activeMatchedText, activeHighlight) }} />
        </div>
      )}

    </div>
  )
}
