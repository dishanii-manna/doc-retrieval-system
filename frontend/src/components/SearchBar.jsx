import { useState, useRef, useEffect } from 'react'
import { Search, X } from 'lucide-react'
import { getSuggestions } from '../services/api'

export default function SearchBar({ onSearch, initialQuery = '' }) {
  const [query, setQuery] = useState(initialQuery)
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const debounceRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (query.length < 2) { setSuggestions([]); return }
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await getSuggestions(query)
        setSuggestions(data.suggestions || [])
        setShowSuggestions(true)
      } catch { setSuggestions([]) }
    }, 300)
    return () => clearTimeout(debounceRef.current)
  }, [query])

  const handleSubmit = (e) => {
    e.preventDefault()
    setShowSuggestions(false)
    if (query.trim()) onSearch(query.trim())
  }

  const handleSuggestion = (s) => {
    setQuery(s.book_title)
    setShowSuggestions(false)
    onSearch(s.book_title)
  }

  const clear = () => { setQuery(''); setSuggestions([]); inputRef.current?.focus() }

  return (
    <div className="relative w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400" size={20} />
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onFocus={() => suggestions.length && setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
            placeholder="Search across all books..."
            className="w-full pl-12 pr-10 py-3 rounded-xl border-2 border-stone-300
                       bg-white focus:outline-none focus:border-amber-500
                       font-['Source_Serif_4'] text-lg shadow-sm"
          />
          {query && (
            <button type="button" onClick={clear}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-700">
              <X size={18} />
            </button>
          )}
        </div>
        <button type="submit"
          className="px-6 py-3 bg-amber-700 hover:bg-amber-800 text-white
                     rounded-xl font-semibold transition-colors shadow-sm">
          Search
        </button>
      </form>

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <ul className="absolute z-50 w-full mt-1 bg-white border border-stone-200
                       rounded-xl shadow-lg overflow-hidden">
          {suggestions.map((s, i) => (
            <li key={i}
              onMouseDown={() => handleSuggestion(s)}
              className="px-4 py-3 hover:bg-amber-50 cursor-pointer border-b border-stone-100 last:border-0">
              <div className="font-medium text-stone-800">{s.book_title}</div>
              <div className="text-sm text-stone-500">{s.author}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
