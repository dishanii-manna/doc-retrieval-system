import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listBooks } from '../services/api'
import { BookOpen, Calendar, Building, Loader2, Search } from 'lucide-react'

export default function BooksPage() {
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterText, setFilterText] = useState('')

  useEffect(() => {
    listBooks()
      .then(setBooks)
      .catch(() => setBooks([]))
      .finally(() => setLoading(false))
  }, [])

  const filtered = books.filter(b =>
    b.title.toLowerCase().includes(filterText.toLowerCase()) ||
    b.author.toLowerCase().includes(filterText.toLowerCase())
  )

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-['Playfair_Display'] text-3xl font-bold text-stone-800">
          Library ({books.length} books)
        </h1>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-stone-400" size={16} />
          <input
            value={filterText}
            onChange={e => setFilterText(e.target.value)}
            placeholder="Filter by title or author…"
            className="pl-9 pr-4 py-2 border border-stone-300 rounded-lg text-sm focus:outline-none focus:border-amber-500"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center mt-16">
          <Loader2 className="animate-spin text-amber-600" size={32} />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(book => (
            <Link
              key={book.doc_id}
              to={`/books/${book.doc_id}`}
              className="bg-white border border-stone-200 rounded-xl p-5 hover:border-amber-400
                         hover:shadow-md transition-all group"
            >
              <div className="flex items-start gap-3">
                <div className="w-10 h-12 bg-amber-100 rounded flex items-center justify-center shrink-0 group-hover:bg-amber-200 transition-colors">
                  <BookOpen size={20} className="text-amber-700" />
                </div>
                <div className="min-w-0">
                  <h3 className="font-['Playfair_Display'] font-semibold text-stone-800 leading-tight line-clamp-2">
                    {book.title}
                  </h3>
                  <p className="text-sm text-stone-500 mt-1 truncate">{book.author}</p>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2 text-xs text-stone-400">
                {book.year && (
                  <span className="flex items-center gap-1">
                    <Calendar size={11} />{book.year}
                  </span>
                )}
                {book.publisher && (
                  <span className="flex items-center gap-1 truncate">
                    <Building size={11} />{book.publisher}
                  </span>
                )}
                <span className="ml-auto text-amber-600">{book.paragraph_count} paragraphs</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="text-center mt-16 text-stone-400">
          <BookOpen size={40} className="mx-auto mb-2 opacity-30" />
          <p>No books found.</p>
        </div>
      )}
    </div>
  )
}
