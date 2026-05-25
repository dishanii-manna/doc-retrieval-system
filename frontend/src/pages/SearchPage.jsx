import { useState, useCallback, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import ResultCard from '../components/ResultCard'
import PdfViewer from '../components/PdfViewer'
import { searchParagraphs } from '../services/api'
import { BookOpen, Loader2, SlidersHorizontal } from 'lucide-react'

export default function SearchPage() {
  const [searchParams] = useSearchParams()
  const [results, setResults] = useState([])
  const [total, setTotal] = useState(0)
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({ author: '', year_from: '', year_to: '', doc_id: '' })
  const [page, setPage] = useState(0)
  const PAGE_SIZE = 10

  // Reset search state when navigating to home page fresh
  const prevSearch = useRef(searchParams.toString())
  useEffect(() => {
    const current = searchParams.toString()
    if (current === '' && prevSearch.current !== '') {
      setResults([])
      setTotal(0)
      setQuery('')
      setSelected(null)
      setFilters({ author: '', year_from: '', year_to: '', doc_id: '' })
      setShowFilters(false)
      setPage(0)
    }
    prevSearch.current = current
  }, [searchParams])

// Read doc_id from URL when navigating from "Search in this book"
useEffect(() => {
  const docId = searchParams.get('doc_id')
  if (docId) {
    setShowFilters(true)
    // Fetch book metadata to pre-fill filters
    import('../services/api').then(({ getBook }) => {
      getBook(docId).then(book => {
        setFilters(f => ({
          ...f,
          doc_id: docId,
          author: book.author || '',
          year_from: book.year ? String(book.year) : '',
          year_to: book.year ? String(book.year) : '',
        }))
      }).catch(() => {
        setFilters(f => ({ ...f, doc_id: docId }))
      })
    })
  }
}, [searchParams])

  const doSearch = useCallback(async (q, offset = 0) => {
    setLoading(true)
    setError(null)
    try {
      const params = {
        q,
        size: PAGE_SIZE,
        offset,
        ...(filters.author    && { author:    filters.author }),
        ...(filters.year_from && { year_from: filters.year_from }),
        ...(filters.year_to   && { year_to:   filters.year_to }),
        ...(filters.doc_id    && { doc_id:    filters.doc_id }),
      }
      const data = await searchParagraphs(params)
      setResults(data.results)
      setTotal(data.total)
      setQuery(q)
      setPage(offset / PAGE_SIZE)
      if (data.results.length > 0) setSelected(data.results[0])
    } catch (e) {
      setError('Search failed. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }, [filters])

  const handleSearch = (q) => { setSelected(null); doSearch(q, 0) }

  // FilterPanel defined as JSX directly to avoid re-render issues
  const filterPanel = (
    <div className="bg-white border border-stone-200 rounded-xl p-4 mb-4 grid grid-cols-3 gap-3">
      <div>
        <label className="text-xs text-stone-500 mb-1 block">Author</label>
        <input
          value={filters.author}
          onChange={e => setFilters(f => ({ ...f, author: e.target.value }))}
          placeholder="e.g. John Norris"
          className="w-full border border-stone-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-amber-500"
        />
      </div>
      <div>
        <label className="text-xs text-stone-500 mb-1 block">Year from</label>
        <input
          value={filters.year_from}
          onChange={e => setFilters(f => ({ ...f, year_from: e.target.value }))}
          placeholder="1680"
          className="w-full border border-stone-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-amber-500"
        />
      </div>
      <div>
        <label className="text-xs text-stone-500 mb-1 block">Year to</label>
        <input
          value={filters.year_to}
          onChange={e => setFilters(f => ({ ...f, year_to: e.target.value }))}
          placeholder="1710"
          className="w-full border border-stone-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-amber-500"
        />
      </div>
      {filters.doc_id && (
        <div className="col-span-3 flex items-center gap-2 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
          <span>Searching within: <strong>{filters.doc_id}</strong></span>
          <button onClick={() => setFilters(f => ({ ...f, doc_id: '' }))}
            className="ml-auto text-stone-400 hover:text-red-500">✕ Clear</button>
        </div>
      )}
    </div>
  )

  return (
    <div>
      {/* Hero */}
      <div className="text-center mb-8">
        <h1 className="font-['Playfair_Display'] text-4xl font-bold text-stone-800 mb-2">
          Search the Archive
        </h1>
        <p className="text-stone-500 text-lg">Full-text search across digitized historical books</p>
      </div>

      {/* Search bar */}
      <SearchBar onSearch={handleSearch} initialQuery={query} />

      {/* Filter toggle */}
      <div className="flex justify-center mt-3">
        <button onClick={() => setShowFilters(v => !v)}
          className="flex items-center gap-1 text-sm text-stone-500 hover:text-amber-700 transition-colors">
          <SlidersHorizontal size={14} />
          {showFilters ? 'Hide filters' : 'Show filters'}
        </button>
      </div>
      {showFilters && <div className="mt-3">{filterPanel}</div>}

      {/* Error */}
      {error && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center mt-12">
          <Loader2 className="animate-spin text-amber-600" size={32} />
        </div>
      )}

      {/* Empty state */}
      {!loading && query && results.length === 0 && (
        <div className="text-center mt-16 text-stone-400">
          <BookOpen size={48} className="mx-auto mb-3 opacity-30" />
          <p>No results found for "<strong>{query}</strong>"</p>
        </div>
      )}

      {/* Results + PDF split view */}
      {!loading && results.length > 0 && (
        <>
          <p className="text-sm text-stone-500 mt-6 mb-3">
            {total.toLocaleString()} results for "<strong>{query}</strong>"
          </p>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Results list */}
            <div className="space-y-3 overflow-y-auto max-h-[75vh] pr-1">
              {results.map(r => (
                <ResultCard
                  key={r.para_id}
                  result={r}
                  isSelected={selected?.para_id === r.para_id}
                  onSelect={setSelected}
                />
              ))}

              {/* Pagination */}
              <div className="flex justify-between items-center pt-2 pb-1">
                <button
                  disabled={page === 0}
                  onClick={() => doSearch(query, (page - 1) * PAGE_SIZE)}
                  className="text-sm text-amber-700 disabled:opacity-30 hover:underline">
                  ← Previous
                </button>
                <span className="text-xs text-stone-400">Page {page + 1}</span>
                <button
                  disabled={results.length < PAGE_SIZE}
                  onClick={() => doSearch(query, (page + 1) * PAGE_SIZE)}
                  className="text-sm text-amber-700 disabled:opacity-30 hover:underline">
                  Next →
                </button>
              </div>
            </div>

            {/* PDF Viewer */}
            <div className="h-[75vh] sticky top-4">
          {selected ? (
  
 <PdfViewer
  key={selected.para_id}
  docId={selected.doc_id}
  initialPage={selected.page_number}
  highlightText={query}
  matchedText={selected.highlight || selected.text}
/>                       ) : (
                <div className="h-full bg-stone-100 rounded-xl flex items-center justify-center text-stone-400">
                  <div className="text-center">
                    <BookOpen size={40} className="mx-auto mb-2 opacity-30" />
                    <p>Select a result to view its PDF page</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Default state */}
      {!loading && !query && (
        <div className="text-center mt-16 text-stone-400">
          <BookOpen size={56} className="mx-auto mb-4 opacity-20" />
          <p className="text-lg">Enter a search term to explore the archive</p>
        </div>
      )}
    </div>
  )
}
